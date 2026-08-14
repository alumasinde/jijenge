package Validators

import (
	"testing"

	"github.com/alumasinde/jijenge/Auth/DTOs"
)

func TestRegisterValidator(t *testing.T) {
	err := Register(DTOs.RegisterRequest{
		Email: "user@example.com", Password: "a very strong password", FirstName: "Jane", LastName: "Doe",
	})
	if err != nil {
		t.Fatal(err)
	}
	if Register(DTOs.RegisterRequest{Email: "bad", Password: "short", FirstName: "", LastName: ""}) == nil {
		t.Fatal("expected invalid registration")
	}
}

func TestLoginValidator(t *testing.T) {
	if Login(DTOs.LoginRequest{Email: "user@example.com", Password: "password"}) != nil {
		t.Fatal("expected valid login request")
	}
}
