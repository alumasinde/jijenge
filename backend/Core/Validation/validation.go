package Validation

import (
	"errors"
	"fmt"
	"net/mail"
	"strings"
	"unicode/utf8"
)

var (
	ErrRequired      = errors.New("value is required")
	ErrInvalidEmail  = errors.New("invalid email address")
	ErrInvalidLength = errors.New("invalid length")
)

func Required(value, field string) error {
	if strings.TrimSpace(value) == "" {
		return fmt.Errorf("%s: %w", field, ErrRequired)
	}
	return nil
}

func StringLength(value, field string, min, max int) error {
	length := utf8.RuneCountInString(value)
	if length < min || length > max {
		return fmt.Errorf("%s: %w", field, ErrInvalidLength)
	}
	return nil
}

func Email(value string) error {
	value = strings.TrimSpace(value)
	if value == "" {
		return ErrRequired
	}
	address, err := mail.ParseAddress(value)
	if err != nil || address.Address != value || !strings.Contains(value, "@") {
		return ErrInvalidEmail
	}
	return nil
}

// Password performs generic password policy checks.
// Authentication-specific flows should add context-specific rules later.
func Password(value string) error {
	if len([]byte(value)) < 12 {
		return errors.New("password must contain at least 12 bytes")
	}
	if len([]byte(value)) > 128 {
		return errors.New("password must not exceed 128 bytes")
	}
	return nil
}
