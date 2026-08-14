package Escrow

import (
	"github.com/alumasinde/jijenge/Escrow/Handlers"
	"net/http"
)

func RegisterRoutes(mux *http.ServeMux, h *Handlers.Handler) {
	mux.HandleFunc("POST /api/v1/escrows", h.Fund)
	mux.HandleFunc("POST /api/v1/escrows/{id}/dispute", h.Dispute)
}
