FROM rust:1.75-bookworm AS builder

WORKDIR /build

RUN apt-get update && apt-get install -y pkg-config libssl-dev

COPY Cargo.toml ./
COPY src/ ./src/

RUN cargo build --release

FROM debian:bookworm-slim

RUN apt-get update && apt-get install -y ca-certificates libssl3 && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY --from=builder /build/target/release/aegnt-unltd /app/
COPY memory /app/memory
COPY knowledge /app/knowledge

ENV RUST_LOG=info

EXPOSE 8080

CMD ["/app/aegnt-unltd"]
