use axum::{
    routing::{get, post},
    Router,
};
use serde::{Deserialize, Serialize};
use std::net::SocketAddr;
use std::sync::Arc;
use tokio::sync::RwLock;

mod brain;

use brain::{Brain, BrainConfig, SharedBrain};

#[derive(Deserialize)]
struct ProcessRequest {
    input: String,
}

#[derive(Serialize)]
struct ProcessResponse {
    intent: String,
    system: String,
    content: String,
    reasoning_trace: Option<String>,
    latency_ms: u64,
}

async fn process_directive(
    brain: axum::extract::State<SharedBrain>,
    axum::extract::Json(payload): axum::extract::Json<ProcessRequest>,
) -> axum::Json<ProcessResponse> {
    let response = brain.process_directive(&payload.input).await;
    
    axum::Json(ProcessResponse {
        intent: format!("{:?}", response.intent),
        system: response.system,
        content: response.content,
        reasoning_trace: response.reasoning_trace,
        latency_ms: response.latency_ms,
    })
}

async fn health() -> &'static str {
    "OK"
}

#[tokio::main]
async fn main() {
    let config = BrainConfig {
        fast_model: "ollama:llama3".to_string(),
        slow_model: "gemini-3.1-pro".to_string(),
        memory_path: std::path::PathBuf::from("./memory"),
        knowledge_path: std::path::PathBuf::from("./knowledge"),
    };
    
    let brain = Arc::new(Brain::new(config));
    
    // Load system prompt if exists
    let _ = brain.load_system_prompt(&std::path::PathBuf::from("./system_prompt.md")).await;
    
    let app = Router::new()
        .route("/", get(health))
        .route("/process", post(process_directive))
        .with_state(brain);
    
    let addr = SocketAddr::from(([0, 0, 0, 0], 3000));
    println!("🚀 AEGNT-UNLTD running on http://{}", addr);
    
    let listener = tokio::net::TcpListener::bind(addr).await.unwrap();
    axum::serve(listener, app).await.unwrap();
}
