from django.db import models
from django.contrib.auth.models import User
from django.utils.translation import gettext_lazy as _
from django.utils import timezone
from django.utils.text import slugify
from rest_framework.authtoken.models import Token


class ArticleQuerySet(models.QuerySet):
    def published(self):
        return self.filter(is_active=True, pub_date__lte=timezone.now())


class Article(models.Model):
    title = models.CharField(
        max_length=128,
        unique=True,
        help_text=_("Title should be unique and under 128 char."),
    )
    json_body = models.JSONField(
        help_text=_("All content of body should be save base on json."),
    )
    pub_date = models.DateTimeField(default=timezone.now)
    is_active = models.BooleanField(default=False)
    slug = models.SlugField(allow_unicode=True, unique=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE)

    objects = ArticleQuerySet.as_manager()

    class Meta:
        ordering = ["-pub_date",]
        indexes = [
            models.Index(fields=["title", "pub_date", "is_active"])
        ]
        verbose_name_plural = "articles"

    def save(self, *args, **kwargs):
        self.slug = slugify(f"{self.title}-{self.pub_date}")
        super().save(*args, **kwargs)

    def __str__(self):
        return self.title


class ExpiredTokenProxy(Token):
    class Meta:
        proxy = True

    @property
    def is_expired(self):
        return self.created <= timezone.now() - timezone.timedelta(minutes=15)