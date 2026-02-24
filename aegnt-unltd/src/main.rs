use axum::{
    routing::{get, post},
    Router,
};
use serde::{Deserialize, Serialize};
use std::{net::SocketAddr, sync::Arc};
use tokio::sync::RwLock;

#[derive(Debug, Clone, Serialize, Deserialize)]
pub enum Intent {
    QuickAction,
    Strategy,
    Unknown,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct Response {
    pub intent: Intent,
    pub system: String,
    pub content: String,
    pub reasoning_trace: Option<String>,
    pub latency_ms: u64,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct BrainConfig {
    pub fast_model: String,
    pub slow_model: String,
}

pub struct Brain {
    config: BrainConfig,
    system_prompt: RwLock<String>,
}

impl Brain {
    pub fn new(config: BrainConfig) -> Self {
        Self {
            config,
            system_prompt: RwLock::new(String::new()),
        }
    }

    pub async fn process_directive(&self, input: &str) -> Response {
        let start = std::time::Instant::now();
        
        let intent = classify_intent(input);
        
        let (system, content, reasoning_trace) = match intent {
            Intent::QuickAction | Intent::Unknown => {
                (format!("cortex"), format!("[CORTEX] {}\n\nI understand: {}\n\nHow would you like me to help with this?", 
                    if input.len() < 30 { input } else { "Processing your request" }, input), None)
            }
            Intent::Strategy => {
                let trace = Some("1. Intent classified as Strategy\n2. Loading knowledge base\n3. Analyzing patterns\n4. Generating strategic plan".to_string());
                (format!("deep"), format!("[DEEP MIND] Strategic analysis: {}\n\nAnalyzing your request...\n\nI understand you're looking for a strategic approach. Let me work through this systematically.\n\nKey considerations:\n• Context: {}\n• Potential approaches: 3\n• Recommended path: Developing comprehensive strategy", input.len(), input), trace)
            }
        };
        
        let latency_ms = start.elapsed().as_millis() as u64;
        
        Response {
            intent,
            system,
            content,
            reasoning_trace,
            latency_ms,
        }
    }
}

fn classify_intent(input: &str) -> Intent {
    let input_lower = input.to_lowercase();
    
    if input_lower.contains("plan") 
        || input_lower.contains("strategy") 
        || input_lower.contains("analyze")
        || input_lower.contains("build architecture")
        || input_lower.contains("design")
        || input_lower.contains("roadmap")
        || input_lower.contains("approach") {
        Intent::Strategy
    } else {
        Intent::QuickAction
    }
}

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
    brain: axum::extract::State<Arc<Brain>>,
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
    };
    
    let brain = Arc::new(Brain::new(config));
    
    let app = Router::new()
        .route("/", get(health))
        .route("/process", post(process_directive))
        .with_state(brain);
    
    let addr = SocketAddr::from(([0, 0, 0, 0], 8080));
    println!("🚀 AEGNT-UNLTD running on http://{}", addr);
    
    let listener = tokio::net::TcpListener::bind(addr).await.unwrap();
    axum::serve(listener, app).await.unwrap();
}
