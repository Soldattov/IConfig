
from django.db import models
from django.conf import settings


class Feedback(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,  
        on_delete=models.CASCADE,
        verbose_name="Пользователь"
    )
    title = models.CharField(max_length=255, verbose_name="Заголовок отзыва")
    content = models.TextField(verbose_name="Отзыв")
    email_visible = models.BooleanField(default=False, verbose_name="Показывать электронную почту")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Дата публикации")
    
    def __str__(self):
        return f"{self.title} от {self.user.username}"

class Attachment(models.Model):
    feedback = models.ForeignKey(
        Feedback,
        on_delete=models.CASCADE,
        related_name='attachments',
        verbose_name="Отзыв"
    )
    image = models.ImageField(
        upload_to='feedback_attachments/',
        verbose_name="Загруженное изображение"
    )

    def __str__(self):
        return f"Вложение для отзыва {self.feedback.title}"
