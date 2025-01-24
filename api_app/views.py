from http import HTTPMethod

from django.shortcuts import get_object_or_404
from django.utils.translation import gettext_lazy as _
from django.contrib.auth import authenticate
from rest_framework import viewsets, status, permissions
from rest_framework.decorators import action
from rest_framework.authentication import get_authorization_header
from rest_framework.response import Response

from .models import Article, ExpiredTokenProxy
from .serializers import (
    ArticleSerializer,
    UserLoginSerializer,
    AdminArticlesSerializer
)
from .authentication import TokenNotExpiredAuth


class BaseTokenAuthViewSet(viewsets.ViewSet):
    """
        This path is use for user login and tokens refresh.
    """
    model = ExpiredTokenProxy
    serializer_class = UserLoginSerializer

    def user_check(self, request) -> tuple:
        """
            User validation and authorization,
            this function return ( Response(), user ),
            If the user is valid, the response will be None,
            If the user is not valid, the user will be None.
        """

        serializer = self.serializer_class(data=request.data)
        if not serializer.is_valid():
            return (
                Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST),
                None,
            )
        user = authenticate(
            request,
            username=serializer.validated_data["username"],
            password=serializer.validated_data["password"],
        )
        if user is None:
            return (
                Response(
                    {"Error": _("Invalid username or password.")},
                    status=status.HTTP_404_NOT_FOUND,
                ),
                user,
            )
        return (None, user)

    @action(detail=False, methods=[HTTPMethod.POST])
    def login(self, request, format=None):
        """
            This method is use for generating new token,
            if user does not have token or it is expired.
        """
        response, user = self.user_check(request)

        if response:
            return response

        if self.model.objects.filter(user=user).exists():
            token = get_object_or_404(self.model, user=user)
            if token.is_expired:
                token.delete()
                token = self.model.objects.create(user=user)
        else:
            token = self.model.objects.create(user=user)

        return Response({"Token": "Token " + token.key})

    @action(detail=False, methods=[HTTPMethod.PUT])
    def refresh(self, request, format=True):
        """
            This method is use for refreshing token.
        """
        response, user = self.user_check(request)

        if response:
            return response

        queryset = self.model.objects.filter(user=user)
        if queryset.exists():
            queryset.delete()

        token = self.model.objects.create(user=user)
        return Response({"Token": "Token " + token.key})


class ArticleListViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Article.objects.published()
    serializer_class = ArticleSerializer
    lookup_field = "slug"


def get_user_from_token(request) -> tuple:
    """
        this method return user from token on http header.
    """
    auth = get_authorization_header(request).split()

    try:
        token = ExpiredTokenProxy.objects.get(key=auth[1].decode())
        return (None, token.user)
    except:
        return (Response(status=status.HTTP_404_NOT_FOUND), None)


class UserArticleViewSet(viewsets.ViewSet):
    model = Article
    serializer_class = ArticleSerializer
    authentication_classes = [TokenNotExpiredAuth]
    permission_classes = [permissions.IsAuthenticated]
    lookup_field = 'slug'

    def list(self, request, format=True):
        """
            this method return user articles list.
        """
        response, user = get_user_from_token(request)

        if response:
            return response

        queryset = self.model.objects.filter(user=user)
        serializer = self.serializer_class(queryset, many=True)
        return Response(serializer.data)

    def create(self, request, format=None):
        """
            this method create article base on user.
        """
        response, user = get_user_from_token(request)

        if response:
            return response

        try:
            serializer = self.serializer_class(data=request.data)
            if serializer.is_valid():
                serializer.save(user=user)
                print(2)
                return Response(serializer.data, status=status.HTTP_201_CREATED)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        except:
            return Response(status=status.HTTP_404_NOT_FOUND)

    def retrieve(self, request, slug, format="None"):
        response, user = get_user_from_token(request)

        if response:
            return response

        try:
            article = self.model.objects.get(slug=slug, user=user)
            serializer = self.serializer_class(article)
            return Response(serializer.data)
        except:
            return Response(status=status.HTTP_404_NOT_FOUND)

    def update(self, request, slug, format=None):
        response, user = get_user_from_token(request)

        if response:
            return response

        try:
            article = self.model.objects.get(slug=slug, user=user)
            serializer = self.serializer_class(article, data=request.data)
            if serializer.is_valid():
                serializer.save()
                return Response(serializer.data, status=status.HTTP_202_ACCEPTED)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        except:
            return Response(status=status.HTTP_404_NOT_FOUND)

    def destroy(self, request, slug, format=None):
        response, user = get_user_from_token(request)

        if response:
            return Response

        try:
            article = Article.objects.get(slug=slug, user=user)
            article.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)
        except:
            return Response(status=status.HTTP_404_NOT_FOUND)


class AdminArticleViewSet(viewsets.ViewSet):
    model = Article
    serializer_class = AdminArticlesSerializer
    authentication_classes = [TokenNotExpiredAuth]
    permission_classes = [permissions.IsAuthenticated]
    lookup_field = 'slug'

    @action(detail=False, methods=[HTTPMethod.GET])
    def articles(self, request, format=None):
        response, user = get_user_from_token(request)

        if response:
            return response
        if not user.is_superuser:
            return Response(status=status.HTTP_403_FORBIDDEN)

        articles = Article.objects.all()
        serializer = self.serializer_class(articles, many=True)

        return Response(serializer.data)

    @action(detail=True, methods=[HTTPMethod.POST])
    def active_article(self, request, slug, format=None):
        response, user = get_user_from_token(request)

        if response:
            return response
        if not user.is_superuser:
            return Response(status=status.HTTP_403_FORBIDDEN)

        try:
            article = Article.objects.get(slug=slug)
            serializer = self.serializer_class(article, data=request.data)
            if serializer.is_valid():
                serializer.save()
                return Response(status=status.HTTP_202_ACCEPTED)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        except:
            return Response(status=status.HTTP_404_NOT_FOUND)