package Validation

import "testing"

func TestValidation(t *testing.T) {
	if err := Required("  ", "name"); err == nil {
		t.Fatal("expected required error")
	}
	if err := StringLength("abc", "name", 2, 4); err != nil {
		t.Fatal(err)
	}
	if err := Email("user@example.com"); err != nil {
		t.Fatal(err)
	}
	if err := Email("not-an-email"); err == nil {
		t.Fatal("expected invalid email")
	}
	if err := Password("short"); err == nil {
		t.Fatal("expected short password to fail")
	}
}
