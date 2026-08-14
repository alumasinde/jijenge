package Tasks

import (
	"github.com/alumasinde/jijenge/Tasks/Handlers"
	"net/http"
)

func RegisterRoutes(mux *http.ServeMux, h *Handlers.Handler) {
	mux.HandleFunc("POST /api/v1/tasks", h.Create)
	mux.HandleFunc("POST /api/v1/tasks/{id}/publish", h.Publish)
	mux.HandleFunc("POST /api/v1/tasks/{id}/start", h.Start)
	mux.HandleFunc("POST /api/v1/tasks/{id}/complete", h.Complete)
	mux.HandleFunc("POST /api/v1/tasks/{id}/cancel", h.Cancel)
	mux.HandleFunc("POST /api/v1/tasks/{id}/applications", h.Apply)
	mux.HandleFunc("POST /api/v1/applications/{id}/accept", h.AcceptApplication)
	mux.HandleFunc("POST /api/v1/assignments/{id}/submit", h.Submit)
	mux.HandleFunc("POST /api/v1/assignments/{id}/verify", h.Verify)
}
