

from django.shortcuts import render, redirect
from .forms import FeedbackForm
from .models import Feedback

def feedback_view(request):
    if not request.user.is_authenticated:
        return render(request, 'feedback.html', {'show_login_modal': True})
    
    if request.method == 'POST':
        form = FeedbackForm(request.POST, request.FILES)
        if form.is_valid():
            feedback = form.save(commit=False)
            feedback.user = request.user
            feedback.save()
            if hasattr(form, '_attachment') and form._attachment:
                from .models import Attachment
                Attachment.objects.create(feedback=feedback, image=form._attachment)
            return redirect('feedback')
    else:
        form = FeedbackForm()

    feedbacks = Feedback.objects.all().order_by('-created_at')
    context = {
        'form': form,
        'feedbacks': feedbacks,
        'show_login_modal': False
    }
    return render(request, 'feedback.html', context)
