import sqlite3
import json
import time
from typing import Dict, Any, List, Optional
from config import DB_PATH

class ProjectStorage:
    @staticmethod
    def init_db():
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS demo_projects (
            project_id TEXT PRIMARY KEY,
            prompt TEXT NOT NULL,
            pipeline_results TEXT NOT NULL, -- serialized JSON of FinalCompiledApplication
            latency REAL NOT NULL,
            execution_mode TEXT NOT NULL,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL
        );
        """)
        conn.commit()
        conn.close()

    @staticmethod
    def save_project(project_id: str, prompt: str, pipeline_results: Dict[str, Any], latency: float, execution_mode: str) -> None:
        ProjectStorage.init_db()
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        now = time.strftime("%Y-%m-%dT%H:%M:%S")
        
        # Check if project exists
        cursor.execute("SELECT 1 FROM demo_projects WHERE project_id = ?", (project_id,))
        exists = cursor.fetchone()
        
        results_str = json.dumps(pipeline_results)
        if exists:
            cursor.execute("""
            UPDATE demo_projects
            SET prompt = ?, pipeline_results = ?, latency = ?, execution_mode = ?, updated_at = ?
            WHERE project_id = ?
            """, (prompt, results_str, latency, execution_mode, now, project_id))
        else:
            cursor.execute("""
            INSERT INTO demo_projects (project_id, prompt, pipeline_results, latency, execution_mode, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (project_id, prompt, results_str, latency, execution_mode, now, now))
        conn.commit()
        conn.close()

    @staticmethod
    def get_project(project_id: str) -> Optional[Dict[str, Any]]:
        ProjectStorage.init_db()
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("""
        SELECT project_id, prompt, pipeline_results, latency, execution_mode, created_at, updated_at
        FROM demo_projects
        WHERE project_id = ?
        """, (project_id,))
        row = cursor.fetchone()
        conn.close()
        
        if row:
            return {
                "project_id": row[0],
                "prompt": row[1],
                "pipeline_results": json.loads(row[2]),
                "latency": row[3],
                "execution_mode": row[4],
                "created_at": row[5],
                "updated_at": row[6]
            }
        return None

    @staticmethod
    def get_all_projects() -> List[Dict[str, Any]]:
        ProjectStorage.init_db()
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("""
        SELECT project_id, prompt, pipeline_results, latency, execution_mode, created_at, updated_at
        FROM demo_projects
        ORDER BY updated_at DESC
        """)
        rows = cursor.fetchall()
        conn.close()
        
        projects = []
        for row in rows:
            projects.append({
                "project_id": row[0],
                "prompt": row[1],
                "pipeline_results": json.loads(row[2]),
                "latency": row[3],
                "execution_mode": row[4],
                "created_at": row[5],
                "updated_at": row[6]
            })
        return projects
