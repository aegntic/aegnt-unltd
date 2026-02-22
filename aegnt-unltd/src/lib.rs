use serde::{Deserialize, Serialize};
use std::path::PathBuf;
use std::sync::Arc;
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
    pub memory_path: PathBuf,
    pub knowledge_path: PathBuf,
}

pub struct Brain {
    config: BrainConfig,
    system_prompt: RwLock<String>,
    intent_classifier: IntentClassifier,
}

impl Brain {
    pub fn new(config: BrainConfig) -> Self {
        Self {
            config: config.clone(),
            system_prompt: RwLock::new(String::new()),
            intent_classifier: IntentClassifier::new(),
        }
    }

    pub async fn load_system_prompt(&self, path: &PathBuf) -> Result<(), String> {
        let prompt = tokio::fs::read_to_string(path)
            .await
            .map_err(|e| e.to_string())?;
        
        let mut sp = self.system_prompt.write().await;
        *sp = prompt;
        
        Ok(())
    }

    pub async fn process_directive(&self, input: &str) -> Response {
        let start = std::time::Instant::now();
        
        // 1. Classification (System 1 - The Cortex)
        let intent = self.intent_classifier.classify(input).await;
        
        // 2. Route to appropriate system
        let (system, content, reasoning_trace) = match intent {
            Intent::QuickAction => {
                // System 1: Fast, local model
                self.fast_execute(input).await
            }
            Intent::Strategy => {
                // System 2: Deep reasoning with grounding
                self.deep_reason(input).await
            }
            Intent::Unknown => {
                // Default to System 1 for safety
                self.fast_execute(input).await
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

    async fn fast_execute(&self, input: &str) -> (String, String, Option<String>) {
        // System 1: < 200ms, local Llama via Ollama
        // For now, return mock response
        (
            "cortex".to_string(),
            format!("[FAST] Processed: {}", input),
            None,
        )
    }

    async fn deep_reason(&self, input: &str) -> (String, String, Option<String>) {
        // System 2: Full reasoning with grounding pass
        let reasoning = format!("[DEEP] Analyzing strategy for: {}", input);
        
        // Grounding pass would happen here
        let trace = Some(format!(
            "1. Loaded knowledge from {:?}\n2. Grounding against constitution\n3. Generated plan",
            self.config.knowledge_path
        ));
        
        (
            "deep_mind".to_string(),
            reasoning,
            trace,
        )
    }
}

struct IntentClassifier {
    // Lightweight classifier for fast intent detection
}

impl IntentClassifier {
    fn new() -> Self {
        Self {}
    }

    async fn classify(&self, input: &str) -> Intent {
        // Simple keyword-based classification
        // In production: use a tiny local model
        let input_lower = input.to_lowercase();
        
        if input_lower.contains("plan") 
            || input_lower.contains("strategy") 
            || input_lower.contains("analyze")
            || input_lower.contains("build architecture")
            || input_lower.contains("design") {
            Intent::Strategy
        } else if input_lower.contains("what")
            || input_lower.contains("how")
            || input_lower.len() < 50 {
            Intent::QuickAction
        } else {
            Intent::Unknown
        }
    }
}

pub type SharedBrain = Arc<Brain>;

#[cfg(test)]
mod tests {
    use super::*;

    #[tokio::test]
    async fn test_intent_classification() {
        let classifier = IntentClassifier::new();
        
        let intent = classifier.classify("Build a pricing strategy").await;
        assert_eq!(intent, Intent::Strategy);
        
        let intent = classifier.classify("What time is it?").await;
        assert_eq!(intent, Intent::QuickAction);
    }
}
