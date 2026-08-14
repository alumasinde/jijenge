# syntax=docker/dockerfile:1.7

FROM golang:1.24-bookworm AS builder
WORKDIR /src

COPY go.mod go.sum ./
RUN go mod download

COPY . .
RUN CGO_ENABLED=0 GOOS=linux GOARCH=amd64 go build -tags=mysql -trimpath -ldflags="-s -w" -o /out/jijenge-api ./cmd/api
RUN CGO_ENABLED=0 GOOS=linux GOARCH=amd64 go build -tags=mysql -trimpath -ldflags="-s -w" -o /out/jijenge-migrate ./cmd/migrate

FROM gcr.io/distroless/static-debian12:nonroot AS api
WORKDIR /app
COPY --from=builder /out/jijenge-api /app/jijenge-api
USER nonroot:nonroot
EXPOSE 8080
ENTRYPOINT ["/app/jijenge-api"]

FROM gcr.io/distroless/static-debian12:nonroot AS migrate
WORKDIR /app
COPY --from=builder /out/jijenge-migrate /app/jijenge-migrate
USER nonroot:nonroot
ENTRYPOINT ["/app/jijenge-migrate"]
