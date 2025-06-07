# polls/views.py
from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponse, HttpResponseRedirect
from django.urls import reverse
from django.contrib import messages
from django.db.models import Sum
from .models import Option, Vote, VotedUser
from .forms import NicknameForm


def index(request):
    """
    Стартова сторінка для введення нікнейму, з опціями голосувати або дивитися результати.
    """
    form = NicknameForm()

    if request.method == 'POST':
        if 'vote_button' in request.POST:
            form = NicknameForm(request.POST)
            if form.is_valid():
                nickname = form.cleaned_data['nickname']

                if VotedUser.objects.filter(nickname=nickname).exists():
                    messages.error(request,
                                   f"Нікнейм '{nickname}' вже проголосував. Ви можете проголосувати лише один раз.")
                    return render(request, 'polls/index.html', {'form': form})

                request.session['voter_nickname'] = nickname
                # При новому початку голосування, скидаємо всі тимчасові дані
                request.session['available_scores'] = [3, 2, 1]
                request.session['temp_votes'] = {}
                return redirect('polls:vote')
            else:
                return render(request, 'polls/index.html', {'form': form})

        elif 'results_button' in request.POST:
            return redirect('polls:results')

    return render(request, 'polls/index.html', {'form': form})


def vote_view(request):
    """
    Сторінка для голосування.
    """
    nickname = request.session.get('voter_nickname')
    if not nickname:
        messages.warning(request, "Будь ласка, введіть ваш нікнейм, щоб проголосувати.")
        return redirect('polls:index')

    if VotedUser.objects.filter(nickname=nickname).exists():
        messages.info(request, "Ви вже проголосували. Перегляньте результати.")
        return redirect('polls:results')

    options = Option.objects.all()
    available_scores = request.session.get('available_scores', [3, 2, 1])
    temp_votes = request.session.get('temp_votes', {})

    score_options = [3, 2, 1]

    if request.method == 'POST':
        selected_option_id = request.POST.get('option_id')
        selected_score_str = request.POST.get('score')

        if not selected_option_id or not selected_score_str:
            messages.error(request, "Будь ласка, оберіть варіант та бал.")
            return render(request, 'polls/vote.html', {
                'nickname': nickname,
                'options': options,
                'available_scores': available_scores,
                'temp_votes': temp_votes,
                'score_options': score_options,
            })

        try:
            selected_option_id = int(selected_option_id)
            selected_score = int(selected_score_str)
        except ValueError:
            messages.error(request, "Некоректні дані.")
            return render(request, 'polls/vote.html', {
                'nickname': nickname,
                'options': options,
                'available_scores': available_scores,
                'temp_votes': temp_votes,
                'score_options': score_options,
            })

        if selected_score not in available_scores:
            messages.error(request, f"Бал {selected_score} вже використаний або недоступний.")
            return render(request, 'polls/vote.html', {
                'nickname': nickname,
                'options': options,
                'available_scores': available_scores,
                'temp_votes': temp_votes,
                'score_options': score_options,
            })

        if selected_option_id in temp_votes.values():
            option_already_voted_for = get_object_or_404(Option, id=selected_option_id).text
            messages.error(request,
                           f"Варіант '{option_already_voted_for}' вже отримав бал. Кожен варіант може отримати лише один бал (3, 2 або 1).")
            return render(request, 'polls/vote.html', {
                'nickname': nickname,
                'options': options,
                'available_scores': available_scores,
                'temp_votes': temp_votes,
                'score_options': score_options,
            })

        temp_votes[str(selected_score)] = selected_option_id
        available_scores.remove(selected_score)

        request.session['temp_votes'] = temp_votes
        request.session['available_scores'] = available_scores

        messages.success(request, f"Ви віддали {selected_score} балів за обраний варіант.")

        if not available_scores:
            return redirect('polls:confirm_vote')
        else:
            return redirect('polls:vote')

    return render(request, 'polls/vote.html', {
        'nickname': nickname,
        'options': options,
        'available_scores': available_scores,
        'temp_votes': temp_votes,
        'score_options': score_options,
    })


def confirm_vote(request):
    """
    Сторінка підтвердження голосування після використання всіх балів.
    """
    nickname = request.session.get('voter_nickname')
    temp_votes = request.session.get('temp_votes')

    if not nickname or not temp_votes:
        messages.error(request, "Сесія голосування не знайдена. Будь ласка, почніть знову.")
        return redirect('polls:index')

    if VotedUser.objects.filter(nickname=nickname).exists():
        messages.info(request, "Ви вже проголосували. Перегляньте результати.")
        return redirect('polls:results')

    confirmed_votes_details = []
    total_score_sum = 0

    for score_str, option_id in temp_votes.items():
        score = int(score_str)
        option = get_object_or_404(Option, pk=option_id)
        confirmed_votes_details.append({'option_text': option.text, 'score': score})
        total_score_sum += score

    confirmed_votes_details.sort(key=lambda x: x['score'], reverse=True)

    if request.method == 'POST':
        if 'confirm_button' in request.POST:  # Нова перевірка для кнопки підтвердження
            for score_str, option_id in temp_votes.items():
                score = int(score_str)
                option = get_object_or_404(Option, pk=option_id)
                Vote.objects.create(
                    option=option,
                    voter_nickname=nickname,
                    score=score
                )
            VotedUser.objects.create(nickname=nickname)

            del request.session['voter_nickname']
            del request.session['available_scores']
            del request.session['temp_votes']

            messages.success(request, "Ваші голоси успішно зараховані! Дякуємо за участь.")
            return redirect('polls:results')

        elif 'change_button' in request.POST:  # Якщо натиснута кнопка "Змінити"
            # Скидаємо тимчасові голоси, але зберігаємо нікнейм та доступні бали
            request.session['temp_votes'] = {}
            request.session['available_scores'] = [3, 2, 1]  # Відновлюємо всі бали
            messages.info(request, "Ви можете змінити свій вибір. Будь ласка, проголосуйте знову.")
            return redirect('polls:vote')

    return render(request, 'polls/confirm_vote.html', {
        'nickname': nickname,
        'confirmed_votes_details': confirmed_votes_details,
        'total_score_sum': total_score_sum,
    })


def results_view(request):
    """
    Відображення результатів голосування.
    """
    results = Option.objects.annotate(
        total_score=Sum('vote__score')
    ).order_by('-total_score')

    return render(request, 'polls/results.html', {'results': results})