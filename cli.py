#!/usr/bin/env python3
"""
NexusAgent CLI Client
Command-line interface for managing agents
"""

import asyncio
import argparse
import sys
import json
from typing import Optional

import httpx


API_BASE = "http://localhost:8000"


async def create_agent(
    name: str, model: str = "llama4:70b", tools: str = "terminal,browser,memory"
):
    """Create a new agent"""
    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{API_BASE}/api/agents",
            json={
                "name": name,
                "model": model,
                "tools": tools.split(","),
                "auto_evolve": True,
            },
        )

        if response.status_code == 200:
            data = response.json()
            print(f"✓ Agent created: {data['agent_id']}")
            return data["agent_id"]
        else:
            print(f"✗ Error: {response.text}")
            return None


async def list_agents():
    """List all agents"""
    async with httpx.AsyncClient() as client:
        response = await client.get(f"{API_BASE}/api/agents")

        if response.status_code == 200:
            agents = response.json()
            if not agents:
                print("No agents running")
                return

            print(f"\n{'ID':<12} {'Name':<15} {'Model':<20} {'State':<12} {'Tasks'}")
            print("-" * 70)
            for agent in agents:
                print(
                    f"{agent['id']:<12} {agent['name']:<15} {agent['model']:<20} {agent['state']:<12} {agent.get('execution_steps', 0)}"
                )
        else:
            print(f"✗ Error: {response.text}")


async def execute_task(agent_id: str, task: str):
    """Execute a task on an agent"""
    async with httpx.AsyncClient(timeout=300.0) as client:
        response = await client.post(
            f"{API_BASE}/api/agents/{agent_id}/execute",
            json={"description": task, "context": {}},
        )

        if response.status_code == 200:
            result = response.json()
            print(f"\n✓ Task completed: {result['id']}")
            print(f"Status: {result['status']}")
            if result.get("result"):
                print(f"Result: {json.dumps(result['result'], indent=2)}")
        else:
            print(f"✗ Error: {response.text}")


async def agent_status(agent_id: str):
    """Get agent status"""
    async with httpx.AsyncClient() as client:
        response = await client.get(f"{API_BASE}/api/agents/{agent_id}")

        if response.status_code == 200:
            status = response.json()
            print(f"\nAgent: {status['name']} ({status['id']})")
            print(f"Model: {status['model']}")
            print(f"State: {status['state']}")
            print(f"Tools available: {status['tools_available']}")
            print(f"Tools created: {status['tools_created']}")
            print(f"Execution steps: {status['execution_steps']}")
        else:
            print(f"✗ Error: {response.text}")


async def delete_agent(agent_id: str):
    """Delete an agent"""
    async with httpx.AsyncClient() as client:
        response = await client.delete(f"{API_BASE}/api/agents/{agent_id}")

        if response.status_code == 200:
            print(f"✓ Agent deleted: {agent_id}")
        else:
            print(f"✗ Error: {response.text}")


async def list_models():
    """List available models"""
    async with httpx.AsyncClient() as client:
        response = await client.get(f"{API_BASE}/api/models")

        if response.status_code == 200:
            models = response.json()
            print("\nAvailable Models:")
            for model in models.get("available_models", []):
                print(
                    f"  • {model['name']} (context: {model['context']:,}) - {model['status']}"
                )
        else:
            print(f"✗ Error: {response.text}")


async def system_status():
    """Get system status"""
    async with httpx.AsyncClient() as client:
        response = await client.get(f"{API_BASE}/api/orchestrator")

        if response.status_code == 200:
            status = response.json()
            print(f"\nSystem Status:")
            print(f"  Total agents: {status['total_agents']}")
            print(f"  Active agents: {status['active_agents']}")
            print(f"  Queued tasks: {status['queued_tasks']}")
        else:
            print(f"✗ Error: {response.text}")


async def interactive_mode(agent_id: str):
    """Interactive chat with agent"""
    print(f"\n=== Interactive mode with agent {agent_id} ===")
    print("Type 'exit' to quit, 'clear' to clear history\n")

    async with httpx.AsyncClient(timeout=60.0) as client:
        while True:
            try:
                task = input("You: ")
                if task.lower() in ("exit", "quit"):
                    break
                if task.lower() == "clear":
                    continue

                response = await client.post(
                    f"{API_BASE}/api/agents/{agent_id}/execute",
                    json={"description": task, "context": {}},
                )

                if response.status_code == 200:
                    result = response.json()
                    if result.get("result"):
                        print(f"Agent: {json.dumps(result['result'], indent=2)}\n")
                    else:
                        print(f"Agent: (completed task)\n")
                else:
                    print(f"Error: {response.text}\n")

            except KeyboardInterrupt:
                break
            except Exception as e:
                print(f"Error: {e}\n")


def main():
    parser = argparse.ArgumentParser(description="NexusAgent CLI")
    subparsers = parser.add_subparsers(dest="command", help="Commands")

    # Create agent
    create_parser = subparsers.add_parser("create", help="Create a new agent")
    create_parser.add_argument("name", help="Agent name")
    create_parser.add_argument("--model", default="llama4:70b", help="Model to use")
    create_parser.add_argument(
        "--tools", default="terminal,browser,memory", help="Comma-separated tools"
    )

    # List agents
    subparsers.add_parser("list", help="List all agents")

    # Execute task
    exec_parser = subparsers.add_parser("exec", help="Execute a task")
    exec_parser.add_argument("agent_id", help="Agent ID")
    exec_parser.add_argument("task", help="Task description")

    # Agent status
    status_parser = subparsers.add_parser("status", help="Get agent status")
    status_parser.add_argument("agent_id", help="Agent ID")

    # Delete agent
    delete_parser = subparsers.add_parser("delete", help="Delete an agent")
    delete_parser.add_argument("agent_id", help="Agent ID")

    # List models
    subparsers.add_parser("models", help="List available models")

    # System status
    subparsers.add_parser("system", help="Get system status")

    # Interactive mode
    interact_parser = subparsers.add_parser("chat", help="Interactive chat with agent")
    interact_parser.add_argument("agent_id", help="Agent ID")

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return

    # Run async commands
    if args.command == "create":
        asyncio.run(create_agent(args.name, args.model, args.tools))
    elif args.command == "list":
        asyncio.run(list_agents())
    elif args.command == "exec":
        asyncio.run(execute_task(args.agent_id, args.task))
    elif args.command == "status":
        asyncio.run(agent_status(args.agent_id))
    elif args.command == "delete":
        asyncio.run(delete_agent(args.agent_id))
    elif args.command == "models":
        asyncio.run(list_models())
    elif args.command == "system":
        asyncio.run(system_status())
    elif args.command == "chat":
        asyncio.run(interactive_mode(args.agent_id))


if __name__ == "__main__":
    main()
