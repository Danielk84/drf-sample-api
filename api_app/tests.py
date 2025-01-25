from django.test import TestCase
from django.contrib.auth.models import User
from django.utils import timezone
from rest_framework.test import APIClient
from rest_framework.authtoken.models import Token
from rest_framework import status

from .serializers import (
    UserLoginSerializer,
    ArticleSerializer,
    AdminArticlesSerializer
)
from .models import Article

class BaseTokenAuthViewSetTestCase(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.username="testuser"
        self.password="passtest"
        self.user = User.objects.create_user(username=self.username, password=self.password)
        self.login_url = "/token/login/"
        self.refresh_url = "/token/refresh/"
        self.user_data = {
            "username": self.username,
            "password": self.password,
        }

    def test_generating_new_token(self):
        response = self.client.post(
            path=self.login_url,
            data=self.user_data, 
            format="json",
        )

        login_token = "Token " + Token.objects.get(user=self.user).key
        self.assertEqual(response.data["Token"], login_token)

        response = self.client.put(
            path=self.refresh_url,
            data=self.user_data,
            format="json",
        )
        refresh_token = "Token " + Token.objects.get(user=self.user).key

        self.assertEqual(response.data["Token"], refresh_token)
        self.assertNotEqual(response.data["Token"], login_token)

    def test_login_token_not_expired(self):
        token = "Token " + Token.objects.create(user=self.user).key

        response = self.client.post(
            path=self.login_url,
            data=self.user_data,
            format="json"
        )
        self.assertEqual(response.data["Token"], token)

    def test_token_expired(self):
        token = Token.objects.create(user=self.user)
        token.created = timezone.now() - timezone.timedelta(minutes=16)
        token.save()
        key = token.key

        response = self.client.post(
            path=self.login_url,
            data=self.user_data,
            format="json",
        )
        self.assertNotEqual(response.data["Token"], "Token " + key)

    def test_invalid_user(self):
        user = {"username": "invaliduser", "password": "invalidpass"}

        response = self.client.post(
            path=self.login_url,
            data=user,
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

        response = self.client.put(
            path=self.refresh_url,
            data=user,
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_serializer(self):
        data = {"username": "", "password": ""}
        serializer = UserLoginSerializer(data=data)

        self.assertFalse(serializer.is_valid())
        self.assertEqual(len(serializer.errors), 2)


class ArticleListViewSetTestCase(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.username="testuser"
        self.password="passtest"
        self.user = User.objects.create_user(username=self.username, password=self.password)
        for i in range(10):
            setattr(
                self,
                f"article{i}",
                Article.objects.create(
                    title=f"article{i}",
                    json_body="{'body': 'body'}",
                    is_active=i % 2 == 0,
                    user=self.user,
                ),
            )
        self.url = "/articles/"

    def test_active_article(self):
        response = self.client.get(
            path=self.url,
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        serializer = ArticleSerializer(data=response.data, many=True)

        self.assertTrue(serializer.is_valid())
        self.assertEqual(len(serializer.validated_data), 5)

    def test_article_published(self):
        response = self.client.get(
            path=self.url + self.article2.slug + "/",
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["title"], self.article2.title)

    def test_article_not_published(self):
        response = self.client.get(
            path=self.url + self.article1.slug + "/",
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)


class UserArticleViewSet(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.username="testuser"
        self.password="passtest"
        self.user = User.objects.create_user(username=self.username, password=self.password)
        self.key = "Token " + Token.objects.create(user=self.user).key
        self.url = "/user-article/"
        self.client.credentials(HTTP_AUTHORIZATION=self.key)
        for i in range(10):
            setattr(
                self,
                f"article{i}",
                Article.objects.create(
                    title=f"article{i}",
                    json_body="{'body': 'body'}",
                    is_active=i % 2 == 0,
                    user=self.user,
                ),
            )

    def test_create_article(self):
        response = self.client.post(
            path=self.url,
            data={
                "title": "this is test title",
                "json_body": '{"body": "body"}',
            }
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(len(response.data), 6)
        self.assertEqual(response.data["user"], self.user.id)

        response = self.client.post(
            path=self.url,
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_list_article(self):
        response = self.client.get(
            path=self.url,
            format="json",
        )
        serializer = ArticleSerializer(data=response.data, many=True)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(serializer.is_valid())
        self.assertEqual(len(serializer.validated_data), 10)

    def test_retrieve_article(self):
        response = self.client.get(
            path=self.url + self.article1.slug + "/",
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["user"], self.user.id)
        self.assertEqual(response.data["title"], self.article1.title)
        
        response = self.client.get(
            path=self.url + "not-invalid-slug" + "/",
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_update_article(self):
        response = self.client.put(
            path=self.url + self.article1.slug + "/",
            data={ "title": "is changed", "json_body": {"body": "body"} },
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_202_ACCEPTED)

        response = self.client.put(
            path=self.url + self.article2.slug + "/",
            body={
                "title": ' '.join(str(i) for i in range(20)),
                "body": ' '.join(str(i) for i in range(20)),
            },
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        response = self.client.put(
            path=self.url + "invalid-slug" + "/",
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_destroy_article(self):
        article_id = self.article3.id

        response = self.client.delete(
            path=self.url + self.article3.slug + "/",
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Article.objects.filter(id=article_id).exists())

        response = self.client.delete(
            path=self.url + "invalid-slug" + "/",
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)


class AdminArticleViewSetTestCase(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.super_user = User.objects.create_superuser(username="testsuperuser", password="passtest")
        self.key1 = "Token " + Token.objects.create(user=self.super_user).key
        self.not_super_user = User.objects.create_user(username="testnotsuperuser", password="passtest")
        self.key2 = "Token " + Token.objects.create(user=self.not_super_user).key
        self.articles_url = "/admin-article/articles/"
        self.active_article_url = "/admin-article/%s/active_article/"
        self.client.credentials(HTTP_AUTHORIZATION=self.key1)
        for i in range(10):
            setattr(
                self,
                f"article{i}",
                Article.objects.create(
                    title=f"article{i}",
                    json_body="{'body': 'body'}",
                    is_active=i % 2 == 0,
                    user=self.not_super_user,
                ),
            )

    def test_articles_list(self):
        response = self.client.get(
            path=self.articles_url,
            format="json",
        )
        serializer = AdminArticlesSerializer(data=response.data, many=True)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(serializer.is_valid())
        self.assertEqual(len(response.data[0]), 4)
        self.assertEqual(len(serializer.validated_data), 10)
        self.assertEqual(len(serializer.validated_data[0]), 1)

    def test_active_article(self):
        response = self.client.post(
            path=self.active_article_url % self.article1.slug,
            data={"is_active": True},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_202_ACCEPTED)

        response = self.client.post(
            path=self.active_article_url % self.article1.slug,
            data={"is_active": False},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_202_ACCEPTED)

        response = self.client.post(
            path=self.active_article_url % 'invalid-slug',
            data={"is_active": True},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

        response = self.client.post(
            path=self.active_article_url % self.article1.slug,
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_not_super_user(self):
        self.client.credentials(HTTP_AUTHORIZATION=self.key2)
        response = self.client.post(
            path=self.active_article_url % self.article1.slug,
            data={"is_active": True},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

        response = self.client.get(
            path=self.articles_url,
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_token_is_expired(self):
        token = Token.objects.get(user=self.super_user)
        token.created = timezone.now() - timezone.timedelta(minutes=16)
        token.save()

        self.client.credentials(HTTP_AUTHORIZATION=self.key1)
        response = self.client.post(
            path=self.active_article_url % self.article1.slug,
            data={"is_active": True},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

        response = self.client.get(
            path=self.articles_url,
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)