from fastapi import FastAPI, HTTPException, Query, status
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime

app = FastAPI(title="CineMagic: Professional Movie Booking System")

class Movie(BaseModel):
    id: int
    title: str
    price: int
    genre: str
    is_active: bool

class MovieCreate(BaseModel):
    title: str = Field(..., min_length=2)
    price: int = Field(..., gt=0)
    genre: str = Field(..., min_length=3)
    is_active: bool = True

class BookingRequest(BaseModel):
    customer_name: str = Field(..., min_length=2)
    movie_id: int = Field(..., gt=0)
    seats: int = Field(..., ge=1, le=10)
    ticket_type: str = Field("standard", pattern="^(standard|premium)$")

movies = [
    {"id": 1, "title": "Inception", "price": 250, "genre": "Sci-Fi", "is_active": True},
    {"id": 2, "title": "The Dark Knight", "price": 300, "genre": "Action", "is_active": True},
    {"id": 3, "title": "Interstellar", "price": 280, "genre": "Sci-Fi", "is_active": False},
    {"id": 4, "title": "Despicable Me", "price": 200, "genre": "Animation", "is_active": True},
    {"id": 5, "title": "The Conjuring", "price": 220, "genre": "Horror", "is_active": True},
    {"id": 6, "title": "Avatar", "price": 350, "genre": "Adventure", "is_active": True},
]

bookings = []
waiting_list = []
booking_counter = 1



def find_movie(movie_id: int):
    return next((m for m in movies if m["id"] == movie_id), None)

def calculate_total(base_price: int, seats: int, t_type: str):
    total = base_price * seats
    if t_type.lower() == "premium":
        total += 150  # Task 9: Premium Surcharge
    return total

@app.get("/")
def welcome():
    return {"message": "Welcome to CineMagic Bookings!"}

@app.get("/movies/summary")
def movie_summary():
    active = len([m for m in movies if m["is_active"]])
    genres = list(set(m["genre"] for m in movies))
    return {"total": len(movies), "active": active, "genres": genres}

@app.get("/movies/filter")
def filter_movies(genre: Optional[str] = None, max_price: Optional[int] = None):
    results = movies
    if genre:
        results = [m for m in results if m["genre"].lower() == genre.lower()]
    if max_price:
        results = [m for m in results if m["price"] <= max_price]
    return results

@app.get("/movies/search")
def search_movies(q: str = Query(..., min_length=2)):
    return [m for m in movies if q.lower() in m["title"].lower() or q.lower() in m["genre"].lower()]

@app.get("/movies/sorted")
def sort_movies(order: str = "asc"):
    return sorted(movies, key=lambda x: x["price"], reverse=(order == "desc"))

@app.get("/movies")
def get_all_movies():
    return {"count": len(movies), "data": movies}

@app.get("/movies/{movie_id}")
def get_movie(movie_id: int):
    movie = find_movie(movie_id)
    if not movie: raise HTTPException(404, "Movie not found")
    return movie

@app.post("/movies", status_code=201)
def add_movie(m: MovieCreate):
    if any(x["title"].lower() == m.title.lower() for x in movies):
        raise HTTPException(400, "Movie already exists")
    new_movie = {"id": len(movies)+1, **m.dict()}
    movies.append(new_movie)
    return new_movie

@app.put("/movies/{movie_id}")
def update_movie(movie_id: int, price: int, is_active: bool):
    movie = find_movie(movie_id)
    if not movie: raise HTTPException(404, "Movie not found")
    movie.update({"price": price, "is_active": is_active})
    return movie

@app.delete("/movies/{movie_id}")
def delete_movie(movie_id: int):
    movie = find_movie(movie_id)
    if not movie: raise HTTPException(404, "Movie not found")
    movies.remove(movie)
    return {"detail": "Movie deleted"}

@app.post("/bookings")
def book_ticket(req: BookingRequest):
    global booking_counter
    movie = find_movie(req.movie_id)
    if not movie: raise HTTPException(404, "Movie not found")
    if not movie["is_active"]: raise HTTPException(400, "Movie is currently not screening")
    
    total = calculate_total(movie["price"], req.seats, req.ticket_type)
    new_booking = {
        "booking_id": booking_counter,
        "customer": req.customer_name,
        "movie": movie["title"],
        "total_bill": total,
        "status": "confirmed"
    }
    bookings.append(new_order := new_booking)
    booking_counter += 1
    return new_order

@app.post("/movies/{movie_id}/waitlist")
def join_waitlist(movie_id: int, name: str):
    movie = find_movie(movie_id)
    if movie and movie["is_active"]: return {"message": "Movie is active, book directly!"}
    waiting_list.append({"movie_id": movie_id, "user": name})
    return {"message": "Added to waitlist"}

@app.patch("/bookings/{booking_id}/cancel")
def cancel_booking(booking_id: int):
    booking = next((b for b in bookings if b["booking_id"] == booking_id), None)
    if not booking: raise HTTPException(404, "Booking not found")
    booking["status"] = "cancelled"
    return booking

@app.get("/bookings/paged")
def get_paged_bookings(page: int = 1, limit: int = 2):
    start = (page - 1) * limit
    return bookings[start : start + limit]

@app.get("/admin/analytics")
def get_analytics():
    revenue = sum(b["total_bill"] for b in bookings if b["status"] == "confirmed")
    return {"total_revenue": revenue, "bookings_count": len(bookings)}

@app.post("/movies/bulk-status")
def bulk_update(ids: List[int], active: bool):
    updated = 0
    for m in movies:
        if m["id"] in ids:
            m["is_active"] = active
            updated += 1
    return {"message": f"Updated {updated} movies"}

# T4: All Bookings
@app.get("/bookings")
def get_all_bookings():
    return bookings