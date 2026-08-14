package Auth

import (
	"net/http"

	"github.com/alumasinde/jijenge/Auth/Handlers"
)

func RegisterRoutes(mux *http.ServeMux, handler *Handlers.AuthHandler) {
	mux.HandleFunc("POST /api/v1/auth/register", handler.Register)
	mux.HandleFunc("POST /api/v1/auth/login", handler.Login)
	mux.HandleFunc("POST /api/v1/auth/refresh", handler.Refresh)
	mux.HandleFunc("POST /api/v1/auth/logout", handler.Logout)
}
