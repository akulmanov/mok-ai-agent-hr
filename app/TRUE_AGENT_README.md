# 🤖 True Agent System

## Overview

The **True Agent** is a fully autonomous AI agent system for HR screening that implements advanced agentic capabilities including:

- **Autonomous Reasoning** (ReAct pattern)
- **Strategic Planning** (Goal decomposition)
- **Dynamic Tool Selection**
- **Memory Management** (Short-term, long-term, episodic)
- **Self-Reflection** and **Adaptation**
- **Confidence-Based Decision Making**

## Architecture

### Core Components

1. **AgentMemory** (`app/agent_memory.py`)
   - Manages working memory, context, and long-term patterns
   - Tracks observations, actions, uncertainties, and confidence
   - Stores successful/failed strategies for learning

2. **AgentPlanner** (`app/agent_planner.py`)
   - Decomposes goals into sub-goals and actionable steps
   - Creates strategic plans with dependencies
   - Adapts plans based on observations

3. **AgentReasoner** (`app/agent_reasoner.py`)
   - Implements ReAct (Reasoning + Acting) pattern
   - Reasons about next actions autonomously
   - Reflects on results and determines next steps
   - Decides when to stop based on confidence

4. **ToolRegistry** (`app/tool_registry.py`)
   - Manages all available tools
   - Enables dynamic tool selection
   - Provides tool descriptions for LLM reasoning

5. **TrueAgent** (`app/true_agent.py`)
   - Grand orchestrator combining all components
   - Executes autonomous screening workflow
   - Manages the full agent loop

## Available Tools

The agent has access to these tools:

1. **evaluate** - Evaluate candidate against position requirements
2. **ask_clarification** - Generate clarification questions
3. **collect_answers** - Collect answers to questions
4. **process_answers** - Process answers and extract structured info
5. **update_profile** - Update candidate profile with new information
6. **reevaluate** - Re-evaluate after profile update
7. **finalize_decision** - Finalize screening decision with confidence check
8. **analyze_candidate** - Deep analysis of candidate profile
9. **analyze_position** - Deep analysis of position requirements
10. **compare** - Compare candidate against multiple positions

## How It Works

### 1. Initialization
```python
agent = TrueAgent(db_session)
```

### 2. Autonomous Screening
```python
screening = agent.run_autonomous_screening(
    candidate_id="candidate_123",
    position_id="position_456",
    max_iterations=10,
    goal="Evaluate candidate with high confidence"
)
```

### 3. Agent Loop Process

For each iteration:

1. **Reasoning**: Agent reasons about current situation, goal, and context
2. **Action Selection**: Agent selects a tool and parameters
3. **Execution**: Tool is executed
4. **Observation**: Results are observed
5. **Reflection**: Agent reflects on results
6. **Memory Update**: Observations, uncertainties, and confidence are updated
7. **Decision**: Agent decides whether to continue or stop

### 4. Stopping Criteria

The agent stops when:
- Maximum iterations reached
- High confidence (≥0.85) with no uncertainties
- Low confidence persists after multiple iterations

## API Usage

### Endpoint: `POST /agent/true-agent`

```json
{
  "candidate_id": "candidate_123",
  "position_id": "position_456",
  "max_iterations": 10,
  "goal": "Evaluate candidate with high confidence (optional)"
}
```

Or with raw job description:

```json
{
  "candidate_id": "candidate_123",
  "raw_job_description": "Looking for a Python developer...",
  "max_iterations": 10
}
```

### Response

Returns a `ScreeningResponse` with the final screening result.

## Key Features

### 1. Autonomous Reasoning
The agent doesn't follow a fixed script. It reasons about:
- What information is needed
- Which tools to use
- What parameters to pass
- When to stop

### 2. Strategic Planning
- Breaks down goals into sub-goals
- Creates step-by-step plans
- Adapts plans based on results

### 3. Memory Management
- **Short-term**: Current session observations and actions
- **Long-term**: Learned patterns and strategies
- **Episodic**: Specific events and outcomes

### 4. Self-Reflection
After each action, the agent:
- Evaluates success/failure
- Identifies new observations
- Tracks uncertainties
- Updates confidence
- Suggests next steps

### 5. Dynamic Tool Selection
The agent chooses tools based on:
- Current goal
- Available context
- Memory state
- Recent observations

## Example Workflow

1. **Initial Evaluation**
   - Agent uses `evaluate` tool
   - Gets initial score and decision
   - Identifies uncertainties

2. **Information Gathering**
   - If uncertainties exist, uses `ask_clarification`
   - Generates questions
   - (In production: collects answers from candidate)

3. **Answer Processing**
   - Uses `process_answers` to extract structured info
   - Updates candidate profile

4. **Re-evaluation**
   - Uses `reevaluate` with updated profile
   - Gets new score

5. **Decision Finalization**
   - Uses `finalize_decision` with confidence check
   - If confidence is high, stops
   - Otherwise, continues gathering information

## Comparison: Simple Agent vs True Agent

### Simple Agent (`run_agent_loop`)
- Fixed sequence: evaluate → ask questions → stop
- No reasoning about next steps
- No adaptation
- No memory management

### True Agent (`run_autonomous_screening`)
- Autonomous reasoning about actions
- Dynamic tool selection
- Strategic planning
- Memory and context management
- Self-reflection and adaptation
- Confidence-based stopping

## Configuration

The agent can be configured via:

- `max_iterations`: Maximum number of iterations (default: 10)
- `goal`: Custom goal for the agent (optional)
- LLM model: Uses `LLMService` with configured model
- Scoring: Uses `ScoringService` with configured thresholds

## Future Enhancements

Potential improvements:
- Multi-agent collaboration (specialist agents)
- Advanced planning with backtracking
- Learning from historical screenings
- Integration with external data sources
- Real-time answer collection from candidates
- Advanced confidence models
- Explainable AI for decisions

## Performance Considerations

- Each iteration makes LLM calls for reasoning and reflection
- Tool execution may involve additional LLM calls
- Memory management is efficient with deque limits
- Consider caching for repeated evaluations

## Logging

The agent provides detailed logging:
- 🤖 Agent initialization
- 🔄 Iteration start
- ⚙️ Tool execution
- ✅ Success
- ❌ Errors
- 🛑 Stopping decisions

Check logs for full agent reasoning process.
