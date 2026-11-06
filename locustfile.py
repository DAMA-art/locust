from faker import Faker
from locust import HttpUser, task, SequentialTaskSet, TaskSet, constant_throughput
import random

fake = Faker('ru_RU')

def auth_headers(token):
    return {
        'Authorization': f'Bearer {token}',
    }

class AdminStaffTasks(TaskSet):

    def on_start(self):
        resp = self.client.post(
            '/api/auth/login',
            json={
                'username': 'vet',
                'password': 'vet12345!',
            },
            name='POST /auth/login (staff)',
        )
        if resp.status_code == 200:
            self.access_token = resp.json()['accessToken']

    @task(5)
    def get_pets(self):
        params = {
            'page': random.randint(1, 3),
            'size': random.choice([5, 10, 20]),
        }
        if random.random() < 0.4:
            params['search'] = random.choice([
                'Барсик', 'Рекс', 'кот', 'собака', 'CHIP',
            ])
        if random.random() < 0.3:
            params['species'] = random.choice(['cat', 'dog'])
        self.client.get(
            '/api/pets',
            params=params,
            headers=auth_headers(self.access_token),
            name='GET /pets',
        )

    @task(5)
    def get_owners(self):
        params = {'page': 1, 'size': 10}
        if random.random() < 0.3:
            params['city'] = random.choice([
                'Москва', 'Санкт-Петербург', 'Казань',
            ])
        self.client.get(
            '/api/owners',
            params=params,
            headers=auth_headers(self.access_token),
            name='GET /owners',
        )

    @task(5)
    def get_clinics(self):
        self.client.get(
            '/api/clinics',
            params={'page': 1, 'size': 10},
            headers=auth_headers(self.access_token),
            name='GET /clinics',
        )

    @task(5)
    def get_services(self):
        params = {'page': 1, 'size': 10}
        if random.random() < 0.5:
            params['clinicId'] = random.randint(1, 3)
        self.client.get(
            '/api/services',
            params=params,
            headers=auth_headers(self.access_token),
            name='GET /services',
        )

    @task(3)
    def get_pet_by_id(self):
        pet_id = random.randint(1, 12)
        self.client.get(
            f'/api/pets/{pet_id}',
            headers=auth_headers(self.access_token),
            name='GET /pets/{id}',
        )

    @task(3)
    def get_visits(self):
        self.client.get(
            '/api/visits',
            headers=auth_headers(self.access_token),
            name='GET /visits',
        )

    @task(2)
    def get_auth_me(self):
        self.client.get(
            '/api/auth/me',
            headers=auth_headers(self.access_token),
            name='GET /auth/me',
        )

    @task(1)
    def create_owner(self):
        payload = {
            'lastName': fake.last_name(),
            'firstName': fake.first_name(),
            'phone': fake.phone_number(),
            'email': fake.unique.email(),
            'city': fake.city_name(),
            'country': 'Россия',
        }
        self.client.post(
            '/api/owners',
            json=payload,
            headers=auth_headers(self.access_token),
            name='POST /owners',
        )

    @task(1)
    def create_pet(self):
        species = random.choice(['cat', 'dog'])
        breeds = {
            'cat': [
                'Британский', 'Сиамская', 'Мейн-кун',
                'Персидская', 'Дворняга',
            ],
            'dog': [
                'Лабрадор', 'Хаски', 'Корги',
                'Пудель', 'Дворняга',
            ],
        }
        payload = {
            'name': fake.first_name(),
            'species': species,
            'breed': random.choice(breeds[species]),
            'chipNumber': f'CHIP-{fake.unique.random_int(10000, 99999)}',
            'ageMonths': random.randint(1, 120),
            'weightKg': round(random.uniform(1.5, 40.0), 1),
            'clinicId': random.randint(1, 3),
            'ownerIds': [random.randint(1, 5)],
            'serviceIds': [random.randint(1, 5)],
            'notes': '',
        }
        self.client.post(
            '/api/pets',
            json=payload,
            headers=auth_headers(self.access_token),
            name='POST /pets',
        )

    @task(1)
    def create_service(self):
        payload = {
            'name': random.choice([
                'Стрижка', 'Мытьё', 'Чистка зубов',
                'SPA', 'Вычёсывание', 'Стрижка когтей',
            ]),
            'description': fake.sentence(nb_words=6),
            'price': random.randint(300, 5000),
            'clinicId': random.randint(1, 3),
        }
        self.client.post(
            '/api/services',
            json=payload,
            headers=auth_headers(self.access_token),
            name='POST /services',
        )

class ClientScenario(SequentialTaskSet):

    @task
    def login_as_client(self):
        resp = self.client.post(
            '/api/auth/login',
            json={
                'username': 'client',
                'password': 'client12!',
            },
            name='POST /auth/login (client)',
        )
        if resp.status_code == 200:
            self.access_token = resp.json()['accessToken']

    @task
    def get_me(self):
        if not self.access_token:
            return
        self.client.get(
            '/api/auth/me',
            headers=auth_headers(self.access_token),
            name='GET /auth/me (client)',
        )

    @task
    def list_visits(self):
        if not self.access_token:
            return
        self.client.get(
            '/api/visits',
            headers=auth_headers(self.access_token),
            name='GET /visits (client)',
        )

    @task
    def try_extend_visit(self):
        if not self.access_token:
            return
        self.client.post(
            '/api/visits/1/extend',
            json={'days': random.randint(1, 5)},
            headers=auth_headers(self.access_token),
            name='POST /visits/{id}/extend',
        )

class ZooUser(HttpUser):
    wait_time = constant_throughput(2)
    tasks = {
        AdminStaffTasks: 4,
        ClientScenario: 1,
    }