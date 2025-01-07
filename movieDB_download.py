from dotenv import load_dotenv
import csv
import time
import requests
import os


# Inicializar CSV si no existe
def initialize_csv(file_name, headers):
    if not os.path.exists(file_name):
        with open(file_name, mode="w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(headers)


# Cargar IDs existentes en un CSV
def load_existing_ids(file_name):
    if not os.path.exists(file_name):
        return set()
    with open(file_name, mode="r", encoding="utf-8") as f:
        reader = csv.reader(f)
        next(reader)  # Saltar el encabezado
        return {row[0] for row in reader}


# Guardar datos en un CSV
def save_to_csv(data, file_name):
    with open(file_name, mode="a", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(data)


# Obtener personas relacionadas con una película
def get_movie_people(movie_id):
    url = f"{BASE_URL}/movie/{movie_id}/credits"
    headers = {
        "accept": "application/json",
        "Authorization": f"Bearer {API_KEY}"  # Usar la clave de autorización
    }
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        return response.json()
    else:
        print(f"Error al obtener personas para la película {movie_id}: {response.status_code}")
        return {"cast": [], "crew": []}


# Obtener imágenes de una película
def get_movie_images(movie_id):
    url = f"{BASE_URL}/movie/{movie_id}/images"
    headers = {
        "accept": "application/json",
        "Authorization": f"Bearer {API_KEY}"
    }
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        return response.json()
    else:
        print(f"Error al obtener imágenes para la película {movie_id}: {response.status_code}")
        return {"backdrops": [], "posters": []}


# Procesar y guardar imágenes de una película
def process_movie_images(movie_id, images_file):
    images_data = get_movie_images(movie_id)
    
    # Procesar backdrops
    for backdrop in images_data.get("backdrops", []):
        save_to_csv([
            movie_id,
            "backdrop",
            backdrop.get("file_path", ""),
            backdrop.get("width", 0),
            backdrop.get("height", 0),
            backdrop.get("aspect_ratio", 0),
            backdrop.get("vote_average", 0),
            backdrop.get("vote_count", 0)
        ], images_file)
    
    # Procesar posters
    for poster in images_data.get("posters", []):
        save_to_csv([
            movie_id,
            "poster",
            poster.get("file_path", ""),
            poster.get("width", 0),
            poster.get("height", 0),
            poster.get("aspect_ratio", 0),
            poster.get("vote_average", 0),
            poster.get("vote_count", 0)
        ], images_file)


# Procesar personas y guardar en CSV
def process_people(people, people_file, existing_people_ids):
    people_ids = []
    for person in people:
        person_id = str(person["id"])
        if person_id not in existing_people_ids:
            save_to_csv([
                person_id,
                person["name"],
                person.get("known_for_department", "Unknown"),
                person.get("popularity", 0),
                person.get("gender", "Unknown"),
                person.get("profile_path", "Unknown")
            ], people_file)
            existing_people_ids.add(person_id)
        people_ids.append(person_id)
    return ";".join(people_ids)


# Función para obtener las películas por página
def get_movies_by_page(page):
    url = f"{BASE_URL}/discover/movie?include_adult=false&include_video=false&language=en-US&sort_by=popularity.desc&page={page}"
    headers = {
        "accept": "application/json",
        "Authorization": f"Bearer {API_KEY}"
    }
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        return response.json().get("results", [])
    else:
        print(f"Error al obtener la página {page}: {response.status_code} - {response.text}")
        return []


# Función para obtener los detalles de una película
def get_movie_details(movie_id):
    url = f"{BASE_URL}/movie/{movie_id}"
    headers = {
        "accept": "application/json",
        "Authorization": f"Bearer {API_KEY}"
    }
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        return response.json()
    else:
        print(f"Error al obtener detalles de la película {movie_id}: {response.status_code} - {response.text}")
        return {}


# Procesar película y guardar toda su información
def process_movie(movie, movies_file, people_file, images_file, existing_movie_ids, existing_people_ids):
    movie_id = str(movie["id"])
    if movie_id not in existing_movie_ids:
        details = get_movie_details(movie_id)
        if details:
            # Obtener y guardar imágenes de la película
            process_movie_images(movie_id, images_file)
            
            # Obtener y procesar personas de la película
            credits = get_movie_people(movie_id)
            cast_ids = process_people(credits["cast"], people_file, existing_people_ids)
            crew_ids = process_people(credits["crew"], people_file, existing_people_ids)
            
            # Guardar información de la película
            save_to_csv([
                details["id"],
                details["title"],
                details.get("release_date", "Unknown"),
                ";".join([genre["name"] for genre in details.get("genres", [])]),
                details.get("popularity", 0),
                details.get("vote_average", 0),
                details.get("overview", "").replace("\n", " "),
                cast_ids,
                crew_ids
            ], movies_file)
            print(f"Película guardada con sus imágenes: {details['title']}")


# Recolectar películas, personas e imágenes
def collect_movies(movies_file, people_file, images_file):
    # Inicializar CSVs si no existen
    initialize_csv(movies_file, ["id", "title", "release_date", "genres", "popularity", "vote_average", "overview", "cast_ids", "crew_ids"])
    initialize_csv(people_file, ["id", "name", "department", "popularity", "gender", "profile_path"])
    initialize_csv(images_file, ["movie_id", "type", "file_path", "width", "height", "aspect_ratio", "vote_average", "vote_count"])

    existing_movie_ids = load_existing_ids(movies_file)
    existing_people_ids = load_existing_ids(people_file)
    page = 1

    while True:
        print(f"Recolectando página {page}...")
        movies = get_movies_by_page(page)

        if not movies:
            print("No hay más páginas disponibles. Finalizando...")
            break

        for movie in movies:
            process_movie(movie, movies_file, people_file, images_file, existing_movie_ids, existing_people_ids)

        page += 1
        time.sleep(1)  # Evitar superar límites de la API


# Configuración inicial
if __name__ == "__main__":
    load_dotenv()
    API_KEY = os.getenv("API_KEY")
    BASE_URL = os.getenv("BASE_URL")
    MOVIES_CSV = os.getenv("MOVIES_CSV")
    PEOPLE_CSV = os.getenv("PEOPLE_CSV")
    IMAGES_CSV = os.getenv("IMAGES_CSV")  

    collect_movies(MOVIES_CSV, PEOPLE_CSV, IMAGES_CSV)