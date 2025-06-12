# polls/views.py

from django.shortcuts import render, redirect
from django.contrib import messages
from .models import Poll, Option, VotedUser, Vote
from .forms import NicknameForm
from django.db.models import Sum  # Імпортуємо Sum для агрегації


# Допоміжна функція для отримання активного опитування
def get_active_poll():
    try:
        return Poll.objects.get(is_active=True)
    except Poll.DoesNotExist:
        return None
    except Poll.MultipleObjectsReturned:
        return Poll.objects.filter(is_active=True).first()


def index(request):
    active_poll = get_active_poll()

    voter_nickname = request.session.get('voter_nickname')
    has_voted = False
    if voter_nickname and active_poll:
        has_voted = VotedUser.objects.filter(poll=active_poll, nickname=voter_nickname).exists()

    nickname_form = NicknameForm()

    context = {
        'voter_nickname': voter_nickname,
        'has_voted': has_voted,
        'active_poll': active_poll,
        'nickname_form': nickname_form,
    }
    return render(request, 'polls/index.html', context)


def set_nickname(request):
    if 'voter_nickname' in request.session:
        del request.session['voter_nickname']

    if 'temp_votes' in request.session:
        del request.session['temp_votes']
    request.session.modified = True

    if request.method == 'POST':
        form = NicknameForm(request.POST)
        if form.is_valid():
            nickname = form.cleaned_data['nickname']
            request.session['voter_nickname'] = nickname
            messages.success(request, f"Нікнейм '{nickname}' успішно встановлено.")
            return redirect('polls:index')
        else:
            messages.error(request, "Будь ласка, введіть коректний нікнейм.")
    else:
        form = NicknameForm()
    return render(request, 'polls/index.html', {'nickname_form': form, 'active_poll': get_active_poll()})


def vote_view(request):
    active_poll = get_active_poll()
    voter_nickname = request.session.get('voter_nickname')

    if not active_poll or not voter_nickname:
        messages.error(request, "Немає активного опитування або не встановлено нікнейм.")
        return redirect('polls:index')

    if VotedUser.objects.filter(poll=active_poll, nickname=voter_nickname).exists():
        messages.info(request, "Ви вже проголосували у цьому опитуванні.")
        return redirect('polls:results')

    # Генеруємо повний список доступних балів на основі min_score_value та max_score_value
    all_possible_scores_in_range = list(range(active_poll.min_score_value, active_poll.max_score_value + 1))

    # Виключаємо 0, якщо дозволені негативні бали
    if active_poll.allow_negative_scores and 0 in all_possible_scores_in_range:
        available_scores_raw = [score for score in all_possible_scores_in_range if score != 0]
    else:
        available_scores_raw = all_possible_scores_in_range

    temp_votes = request.session.get('temp_votes', {})

    if request.method == 'POST':
        option_id = request.POST.get('option_id')
        score_to_assign = request.POST.get('score')

        print(f"DEBUG: Received POST - option_id: {option_id}, score: {score_to_assign}")

        if not option_id or not score_to_assign:
            messages.error(request, "Некоректні дані для голосування.")
            return redirect('polls:vote')

        try:
            option_id = int(option_id)
            score_to_assign_int = int(score_to_assign)
        except ValueError:
            messages.error(request, "Некоректний формат ID варіанта або балу.")
            return redirect('polls:vote')

        # Перевірка, чи бал вже був використаний (ключі temp_votes - це бали)
        if str(score_to_assign_int) in temp_votes:
            messages.warning(request,
                             f"Бал {score_to_assign_int} вже призначений іншому варіанту. Виберіть інший бал або варіант.")
            return redirect('polls:vote')

        # Перевірка, чи варіант вже був вибраний (значення temp_votes - це option_id)
        if option_id in temp_votes.values():
            messages.warning(request, "Цей варіант вже був обраний. Виберіть інший варіант.")
            return redirect('polls:vote')

        # Перевірка, чи бал є одним з доступних (після фільтрації 0)
        if score_to_assign_int not in available_scores_raw:
            messages.error(request, "Недійсний бал.")
            return redirect('polls:vote')

        temp_votes[str(score_to_assign_int)] = option_id
        request.session['temp_votes'] = temp_votes
        request.session.modified = True

        messages.success(request, f"Ви призначили бал {score_to_assign_int} варіанту.")
        return redirect('polls:vote')

    all_options = active_poll.options.all().order_by('id')

    option_id_to_text_map = {option.id: option.text for option in all_options}

    display_options = []
    current_assigned_option_ids = set(temp_votes.values())
    current_used_scores = set(int(s) for s in temp_votes.keys())

    for option in all_options:
        option_data = {
            'id': option.id,
            'text': option.text,
            'assigned_score': None,
            'is_selected': False,
            'available_scores': []
        }

        if option.id in current_assigned_option_ids:
            for score_str, opt_id in temp_votes.items():
                if opt_id == option.id:
                    option_data['assigned_score'] = int(score_str)
                    option_data['is_selected'] = True
                    break

        if not option_data['is_selected']:
            for score in available_scores_raw:  # Перебираємо вже відфільтрований список балів
                if score not in current_used_scores:
                    option_data['available_scores'].append(score)

        display_options.append(option_data)

    all_scores_used = len(temp_votes) == active_poll.num_options_to_vote

    context = {
        'active_poll': active_poll,
        'voter_nickname': voter_nickname,
        'options': display_options,
        'available_scores': available_scores_raw,  # Передаємо відфільтрований список балів
        'temp_votes': temp_votes,
        'all_scores_used': all_scores_used,
        'option_id_to_text_map': option_id_to_text_map,
    }
    return render(request, 'polls/vote.html', context)


def confirm_vote(request):
    active_poll = get_active_poll()
    voter_nickname = request.session.get('voter_nickname')
    temp_votes = request.session.get('temp_votes', {})

    if not active_poll or not voter_nickname or not temp_votes:
        messages.error(request, "Немає даних для підтвердження голосування.")
        return redirect('polls:index')

    confirmed_votes_display = []
    options_queryset = active_poll.options.all()
    options_map = {option.id: option.text for option in options_queryset}

    for score_str, option_id in temp_votes.items():
        try:
            score = int(score_str)
            option_text = options_map.get(option_id, "Невідомий варіант")
            confirmed_votes_display.append({
                'score': score,
                'option_text': option_text
            })
        except ValueError:
            messages.error(request, f"Некоректний бал: {score_str}.")
            return redirect('polls:vote')

    confirmed_votes_display.sort(key=lambda x: x['score'], reverse=True)

    if request.method == 'POST':
        voted_user, created = VotedUser.objects.get_or_create(
            poll=active_poll,
            nickname=voter_nickname
        )

        Vote.objects.filter(voted_user=voted_user).delete()

        for score_str, option_id in temp_votes.items():
            try:
                option = Option.objects.get(pk=option_id)
                score = int(score_str)
                Vote.objects.create(voted_user=voted_user, option=option, score=score)
            except (Option.DoesNotExist, ValueError):
                messages.error(request, "Виникла помилка під час збереження голосів. Спробуйте ще раз.")
                return redirect('polls:vote')

        del request.session['temp_votes']
        request.session.modified = True

        messages.success(request, "Ваші голоси успішно збережено!")
        return redirect('polls:results')

    context = {
        'active_poll': active_poll,
        'voter_nickname': voter_nickname,
        'confirmed_votes': confirmed_votes_display,
    }
    return render(request, 'polls/confirm_vote.html', context)


def results_view(request):
    active_poll = get_active_poll()

    if not active_poll:
        messages.info(request, "Наразі немає активних опитувань для відображення результатів.")
        return redirect('polls:index')

    all_options = active_poll.options.all().order_by('id')

    vote_sums = Vote.objects.filter(
        voted_user__poll=active_poll
    ).values(
        'option__id', 'option__text'
    ).annotate(
        total_score=Sum('score')
    ).order_by('-total_score')

    option_scores_map = {item['option__id']: item['total_score'] for item in vote_sums}

    final_results = []
    for option in all_options:
        total_score = option_scores_map.get(option.id, 0)
        final_results.append({
            'option_text': option.text,
            'total_score': total_score,
        })

    final_results.sort(key=lambda x: x['total_score'], reverse=True)

    voter_nickname = request.session.get('voter_nickname')
    has_voted = False
    if voter_nickname:
        has_voted = VotedUser.objects.filter(poll=active_poll, nickname=voter_nickname).exists()

    context = {
        'active_poll': active_poll,
        'results': final_results,
        'voter_nickname': voter_nickname,
        'has_voted': has_voted,
    }
    return render(request, 'polls/results.html', context)


def change_votes(request):
    if 'temp_votes' in request.session:
        del request.session['temp_votes']
        request.session.modified = True
        messages.info(request, "Ви можете переголосувати.")
    return redirect('polls:vote')


def reset_all_votes(request):
    if request.method == 'POST':
        active_poll = get_active_poll()
        if active_poll:
            VotedUser.objects.filter(poll=active_poll).delete()
            messages.success(request, "Всі голоси для активного опитування скинуто!")
        else:
            messages.warning(request, "Немає активного опитування для скидання голосів.")
    return redirect('polls:index')