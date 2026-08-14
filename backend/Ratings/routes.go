package Ratings

import (
	"github.com/alumasinde/jijenge/Ratings/Handlers"
	"net/http"
)

func RegisterRoutes(mux *http.ServeMux, h *Handlers.Handler) {
	mux.HandleFunc("POST /api/v1/assignments/{id}/ratings", h.Create)
	mux.HandleFunc("GET /api/v1/users/{id}/rating", h.Average)
}
