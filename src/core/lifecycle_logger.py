"""
Lifecycle Event Logger for AI Testing Agent
Tracks and stores all lifecycle events during exploration and execution.
"""
from datetime import datetime
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
from enum import Enum
import json
import os
from pathlib import Path
import uuid


class EventPhase(str, Enum):
    """Lifecycle phases"""
    EXPLORATION = "exploration"
    GENERATION = "generation"
    EXECUTION = "execution"


class EventComponent(str, Enum):
    """System components"""
    FRONTEND = "frontend"
    SERVER = "server"
    SECRETS = "secrets"
    AGENT = "agent"
    BROWSER = "browser"
    LLM = "llm"
    FILESYSTEM = "filesystem"
    EXECUTOR = "executor"


class SecurityContext(BaseModel):
    """Security context for an event"""
    safe: bool = True
    credential_involved: bool = False
    zero_trust: bool = True
    isolation_level: str = "none"


class LifecycleEvent(BaseModel):
    """Structured lifecycle event"""
    event_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    timestamp: datetime = Field(default_factory=datetime.now)
    session_id: str = "default"
    event_type: str  # user_action, browser_init, llm_request, etc.
    phase: EventPhase
    component: EventComponent
    action: str
    description: str = ""
    metadata: Dict[str, Any] = Field(default_factory=dict)
    security_context: SecurityContext = Field(default_factory=SecurityContext)
    duration_ms: Optional[int] = None
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class LifecycleLogger:
    """Singleton logger for lifecycle events"""
    _instance = None
    _events: List[LifecycleEvent] = []
    _current_session_id: str = "default"
    _persist_dir: Path = Path("data/lifecycle_logs")
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(LifecycleLogger, cls).__new__(cls)
            cls._instance._initialize()
        return cls._instance
    
    def _initialize(self):
        """Initialize the logger"""
        # Create persistence directory
        self._persist_dir.mkdir(parents=True, exist_ok=True)
        print(f"[LifecycleLogger] Initialized - Logs dir: {self._persist_dir}")
    
    @classmethod
    def start_session(cls, session_id: str = None):
        """Start a new logging session"""
        instance = cls()
        if session_id:
            instance._current_session_id = session_id
        else:
            instance._current_session_id = f"session_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        print(f"[LifecycleLogger] Session started: {instance._current_session_id}")
        return instance._current_session_id
    
    @classmethod
    def log_event(cls, 
                  event_type: str,
                  phase: EventPhase,
                  component: EventComponent,
                  action: str,
                  description: str = "",
                  metadata: Dict[str, Any] = None,
                  security_context: SecurityContext = None,
                  duration_ms: int = None) -> LifecycleEvent:
        """Log a lifecycle event"""
        instance = cls()
        
        event = LifecycleEvent(
            session_id=instance._current_session_id,
            event_type=event_type,
            phase=phase,
            component=component,
            action=action,
            description=description,
            metadata=metadata or {},
            security_context=security_context or SecurityContext(),
            duration_ms=duration_ms
        )
        
        instance._events.append(event)
        
        # Persist to file (async in production)
        instance._persist_event(event)
        
        print(f"[LifecycleLogger] Event logged: {event_type} - {action}")
        return event
    
    def _persist_event(self, event: LifecycleEvent):
        """Persist event to file"""
        try:
            session_file = self._persist_dir / f"{event.session_id}.jsonl"
            with open(session_file, 'a') as f:
                f.write(event.json() + '\n')
        except Exception as e:
            print(f"[LifecycleLogger] Failed to persist event: {e}")
    
    def _load_events_from_files(self):
        """Load events from persisted JSONL files"""
        try:
            if not self._persist_dir.exists():
                return
            
            # Load all JSONL files
            jsonl_files = sorted(self._persist_dir.glob("*.jsonl"))
            loaded_count = 0
            
            for jsonl_file in jsonl_files:
                try:
                    with open(jsonl_file, 'r') as f:
                        for line in f:
                            if line.strip():
                                event_dict = json.loads(line)
                                # Reconstruct LifecycleEvent from dict
                                event = LifecycleEvent(**event_dict)
                                # Only add if not already in memory
                                if not any(e.event_id == event.event_id for e in self._events):
                                    self._events.append(event)
                                    loaded_count += 1
                except Exception as e:
                    print(f"[LifecycleLogger] Failed to load {jsonl_file}: {e}")
            
            if loaded_count > 0:
                print(f"[LifecycleLogger] Loaded {loaded_count} events from {len(jsonl_files)} files")
        except Exception as e:
            print(f"[LifecycleLogger] Failed to load events from files: {e}")
    
    @classmethod
    def get_events(cls, session_id: str = None, limit: int = None) -> List[LifecycleEvent]:
        """Get all events or filtered by session, sorted by timestamp (latest first)"""
        instance = cls()
        
        # Load from files if memory is empty (e.g., after server reload)
        if len(instance._events) == 0:
            instance._load_events_from_files()
        
        if session_id:
            events = [e for e in instance._events if e.session_id == session_id]
        else:
            events = instance._events
        
        # Sort by timestamp descending (latest first)
        events = sorted(events, key=lambda e: e.timestamp, reverse=True)
        
        if limit:
            events = events[:limit]  # Take first N after sorting
        
        return events
    
    @classmethod
    def get_current_session(cls) -> str:
        """Get current session ID"""
        instance = cls()
        return instance._current_session_id
    
    @classmethod
    def clear_events(cls, session_id: str = None):
        """Clear events"""
        instance = cls()
        
        if session_id:
            instance._events = [e for e in instance._events if e.session_id != session_id]
            print(f"[LifecycleLogger] Cleared events for session: {session_id}")
        else:
            instance._events = []
            print(f"[LifecycleLogger] Cleared all events")
    
    @classmethod
    def get_event_count(cls, session_id: str = None) -> int:
        """Get event count"""
        return len(cls.get_events(session_id))
    
    @classmethod
    def get_sessions(cls) -> List[str]:
        """Get all session IDs"""
        instance = cls()
        sessions = list(set(e.session_id for e in instance._events))
        return sorted(sessions)


# Convenience functions for common event patterns
def log_user_action(action: str, description: str = "", metadata: Dict = None):
    """Log a user action"""
    return LifecycleLogger.log_event(
        event_type="user_action",
        phase=EventPhase.EXPLORATION,
        component=EventComponent.FRONTEND,
        action=action,
        description=description,
        metadata=metadata
    )


def log_server_action(action: str, description: str = "", metadata: Dict = None):
    """Log a server action"""
    return LifecycleLogger.log_event(
        event_type="server_action",
        phase=EventPhase.EXPLORATION,
        component=EventComponent.SERVER,
        action=action,
        description=description,
        metadata=metadata
    )


def log_browser_action(action: str, description: str = "", metadata: Dict = None):
    """Log a browser action"""
    return LifecycleLogger.log_event(
        event_type="browser_action",
        phase=EventPhase.EXPLORATION,
        component=EventComponent.BROWSER,
        action=action,
        description=description,
        metadata=metadata
    )


def log_llm_interaction(action: str, description: str = "", metadata: Dict = None, duration_ms: int = None):
    """Log an LLM interaction"""
    return LifecycleLogger.log_event(
        event_type="llm_interaction",
        phase=EventPhase.EXPLORATION,
        component=EventComponent.LLM,
        action=action,
        description=description,
        metadata=metadata,
        duration_ms=duration_ms
    )


def log_test_execution(action: str, description: str = "", metadata: Dict = None):
    """Log a test execution event"""
    return LifecycleLogger.log_event(
        event_type="test_execution",
        phase=EventPhase.EXECUTION,
        component=EventComponent.EXECUTOR,
        action=action,
        description=description,
        metadata=metadata
    )
