package Validators

import (
	"strings"

	"github.com/alumasinde/jijenge/Auth/DTOs"
	"github.com/alumasinde/jijenge/Core/Validation"
)

func Register(req DTOs.RegisterRequest) error {
	req.Email = strings.TrimSpace(req.Email)
	if err := Validation.Email(req.Email); err != nil {
		return err
	}
	if err := Validation.Password(req.Password); err != nil {
		return err
	}
	if err := Validation.Required(req.FirstName, "first_name"); err != nil {
		return err
	}
	if err := Validation.StringLength(req.FirstName, "first_name", 1, 100); err != nil {
		return err
	}
	if err := Validation.Required(req.LastName, "last_name"); err != nil {
		return err
	}
	return Validation.StringLength(req.LastName, "last_name", 1, 100)
}

func Login(req DTOs.LoginRequest) error {
	if err := Validation.Email(strings.TrimSpace(req.Email)); err != nil {
		return err
	}
	return Validation.Required(req.Password, "password")
}
