import pandas as pd
from pyvis.network import Network

def create_graph_with_genres(csv_path, max_nodes=100):
    # Cargar los datos
    df = pd.read_csv(csv_path).head(max_nodes)
    
    # Crear red con opciones específicas
    net = Network(height='750px', width='100%')
    
    # Configurar la física para más estabilidad y espacio
    net.set_options("""
    {
        "physics": {
            "barnesHut": {
                "gravitationalConstant": -2000,
                "centralGravity": 0.1,
                "springLength": 300,
                "springConstant": 0.01,
                "damping": 0.5
            },
            "stabilization": {
                "enabled": true,
                "iterations": 1000
            }
        },
        "nodes": {
            "shape": "dot",
            "size": 25
        },
        "edges": {
            "smooth": false,
            "length": 300
        }
    }
    """)
    
    # Agregar nodos
    for _, movie in df.iterrows():
        genres = [genre.strip() for genre in movie['genres'].split(';')] if isinstance(movie['genres'], str) else []
        tooltip = f"Título: {movie['title']}\nGéneros: {', '.join(genres)}\nRating: {movie['vote_average']}"
        
        net.add_node(
            movie['id'], 
            label=movie['title'],
            title=tooltip,
            mass=3  # Masa mayor para más estabilidad
        )
    
    # Agregar aristas
    for i, movie1 in df.iterrows():
        genres1 = set(genre.strip() for genre in movie1['genres'].split(';')) if isinstance(movie1['genres'], str) else set()
        
        for j, movie2 in df.iterrows():
            if i >= j:
                continue
                
            genres2 = set(genre.strip() for genre in movie2['genres'].split(';')) if isinstance(movie2['genres'], str) else set()
            
            shared_genres = genres1.intersection(genres2)
            if shared_genres:
                net.add_edge(
                    movie1['id'],
                    movie2['id'],
                    title=f"Géneros compartidos: {', '.join(shared_genres)}",
                    length=300,  # Longitud fija para las aristas
                    width=1  # Aristas más delgadas
                )
    
    # Guardar grafo
    net.save_graph("movie_graph_genres.html")
    print("Grafo guardado como 'movie_graph_genres.html'")

# Uso
if __name__ == "__main__":
    create_graph_with_genres('tmdb_movies.csv')