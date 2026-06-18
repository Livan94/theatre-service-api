import tempfile

from PIL import Image
from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient

from theatre.models import Actor, Genre, Play


PLAYS_URL = reverse("theatre:play-list")


def detail_url(play_id):
    return reverse("theatre:play-detail", args=[play_id])


def image_upload_url(play_id):
    return reverse("theatre:play-upload-image", args=[play_id])


def sample_genre(name="Drama"):
    return Genre.objects.create(name=name)


def sample_actor(first_name="Tom", last_name="Hardy"):
    return Actor.objects.create(first_name=first_name, last_name=last_name)


def sample_play(title="Hamlet", description="Classic tragedy"):
    return Play.objects.create(title=title, description=description)


class PublicPlayApiTests(TestCase):
    def setUp(self):
        self.client = APIClient()

    def test_list_plays(self):
        sample_play(title="Hamlet")
        sample_play(title="Macbeth")

        res = self.client.get(PLAYS_URL)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data["count"], 2)
        self.assertEqual(len(res.data["results"]), 2)

    def test_retrieve_play_detail(self):
        play = sample_play()
        genre = sample_genre()
        actor = sample_actor()
        play.genres.add(genre)
        play.actors.add(actor)

        url = detail_url(play.id)
        res = self.client.get(url)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data["title"], play.title)
        self.assertEqual(len(res.data["genres"]), 1)
        self.assertEqual(len(res.data["actors"]), 1)


class AdminPlayApiTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.admin = get_user_model().objects.create_user(
            email="admin@example.com",
            password="adminpass123",
            is_staff=True,
        )
        self.client.force_authenticate(self.admin)

    def test_create_play_with_relations(self):
        genre1 = sample_genre(name="Drama")
        genre2 = sample_genre(name="Comedy")
        actor1 = sample_actor(first_name="Tom", last_name="Hardy")
        actor2 = sample_actor(first_name="Emma", last_name="Stone")

        payload = {
            "title": "King Lear",
            "description": "Shakespeare play",
            "genre_ids": [genre1.id, genre2.id],
            "actor_ids": [actor1.id, actor2.id],
        }

        res = self.client.post(PLAYS_URL, payload, format="json")

        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        play = Play.objects.get(id=res.data["id"])
        self.assertEqual(play.genres.count(), 2)
        self.assertEqual(play.actors.count(), 2)

    def test_filter_plays_by_genres(self):
        genre1 = sample_genre(name="Drama")
        genre2 = sample_genre(name="Comedy")
        play1 = sample_play(title="Hamlet")
        play2 = sample_play(title="Funny Story")
        play1.genres.add(genre1)
        play2.genres.add(genre2)

        res = self.client.get(PLAYS_URL, {"genres": genre1.id})

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data["count"], 1)
        ids = [item["id"] for item in res.data["results"]]
        self.assertIn(play1.id, ids)
        self.assertNotIn(play2.id, ids)

    def test_filter_plays_by_actors(self):
        actor1 = sample_actor(first_name="Tom", last_name="Hardy")
        actor2 = sample_actor(first_name="Emma", last_name="Stone")
        play1 = sample_play(title="Hamlet")
        play2 = sample_play(title="Funny Story")
        play1.actors.add(actor1)
        play2.actors.add(actor2)

        res = self.client.get(PLAYS_URL, {"actors": actor1.id})

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data["count"], 1)
        ids = [item["id"] for item in res.data["results"]]
        self.assertIn(play1.id, ids)
        self.assertNotIn(play2.id, ids)

    def test_search_play_by_title(self):
        sample_play(title="Hamlet")
        sample_play(title="Macbeth")

        res = self.client.get(PLAYS_URL, {"search": "Ham"})

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data["count"], 1)
        self.assertEqual(len(res.data["results"]), 1)
        self.assertEqual(res.data["results"][0]["title"], "Hamlet")

    def test_upload_image_to_play(self):
        play = sample_play()

        url = image_upload_url(play.id)
        with tempfile.NamedTemporaryFile(suffix=".jpg") as ntf:
            image = Image.new("RGB", (20, 20))
            image.save(ntf, format="JPEG")
            ntf.seek(0)

            res = self.client.post(url, {"image": ntf}, format="multipart")

        play.refresh_from_db()
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertIn("image", res.data)
        self.assertTrue(bool(play.image))

    def test_upload_image_bad_request(self):
        play = sample_play()
        url = image_upload_url(play.id)

        res = self.client.post(url, {"image": "not image"}, format="multipart")

        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    def tearDown(self):
        for play in Play.objects.all():
            if play.image:
                play.image.delete()
