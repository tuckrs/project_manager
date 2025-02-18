from datetime import datetime, timedelta
import networkx as nx
from typing import Dict, List, Optional, Set
from ..models.task import Task, TaskDependency, DependencyType

class SchedulingError(Exception):
    pass

class ProjectScheduler:
    def __init__(self):
        self.graph = nx.DiGraph()
        
    def build_dependency_graph(self, tasks: List[Task], dependencies: List[TaskDependency]):
        """Builds a directed graph representing task dependencies"""
        self.graph.clear()
        
        # Add all tasks as nodes
        for task in tasks:
            self.graph.add_node(
                task.id,
                duration=task.duration or 0,
                earliest_start=None,
                latest_start=None,
                earliest_finish=None,
                latest_finish=None,
                is_milestone=task.is_milestone,
                is_locked=task.is_locked
            )
        
        # Add dependencies as edges
        for dep in dependencies:
            self.graph.add_edge(
                dep.predecessor_id,
                dep.successor_id,
                type=dep.dependency_type,
                lag=dep.lag_time or 0
            )
            
    def detect_cycles(self) -> List[List[int]]:
        """Detects any circular dependencies in the task graph"""
        try:
            cycles = list(nx.simple_cycles(self.graph))
            if cycles:
                return cycles
            return []
        except nx.NetworkXNoCycle:
            return []
            
    def calculate_critical_path(self) -> Dict:
        """Implements the Critical Path Method (CPM) algorithm"""
        if self.detect_cycles():
            raise SchedulingError("Circular dependencies detected")
            
        # Forward pass - earliest times
        sorted_nodes = list(nx.topological_sort(self.graph))
        for node in sorted_nodes:
            predecessors = list(self.graph.predecessors(node))
            if not predecessors:  # Start tasks
                self.graph.nodes[node]['earliest_start'] = 0
            else:
                # Calculate earliest start based on dependencies
                max_predecessor_time = 0
                for pred in predecessors:
                    pred_finish = (self.graph.nodes[pred]['earliest_start'] + 
                                 self.graph.nodes[pred]['duration'])
                    edge_data = self.graph.edges[(pred, node)]
                    if edge_data['type'] == DependencyType.FINISH_TO_START:
                        time = pred_finish + edge_data['lag']
                    elif edge_data['type'] == DependencyType.START_TO_START:
                        time = self.graph.nodes[pred]['earliest_start'] + edge_data['lag']
                    else:  # Handle other dependency types
                        time = pred_finish + edge_data['lag']
                    max_predecessor_time = max(max_predecessor_time, time)
                
                self.graph.nodes[node]['earliest_start'] = max_predecessor_time
                
            # Calculate earliest finish
            self.graph.nodes[node]['earliest_finish'] = (
                self.graph.nodes[node]['earliest_start'] + 
                self.graph.nodes[node]['duration']
            )
            
        # Backward pass - latest times
        project_end = max(
            self.graph.nodes[node]['earliest_finish'] 
            for node in self.graph.nodes
        )
        
        for node in reversed(sorted_nodes):
            successors = list(self.graph.successors(node))
            if not successors:  # End tasks
                self.graph.nodes[node]['latest_finish'] = project_end
            else:
                # Calculate latest finish based on successors
                min_successor_time = float('inf')
                for succ in successors:
                    edge_data = self.graph.edges[(node, succ)]
                    if edge_data['type'] == DependencyType.FINISH_TO_START:
                        time = self.graph.nodes[succ]['latest_start'] - edge_data['lag']
                    elif edge_data['type'] == DependencyType.FINISH_TO_FINISH:
                        time = self.graph.nodes[succ]['latest_finish'] - edge_data['lag']
                    else:
                        time = self.graph.nodes[succ]['latest_start'] - edge_data['lag']
                    min_successor_time = min(min_successor_time, time)
                
                self.graph.nodes[node]['latest_finish'] = min_successor_time
                
            # Calculate latest start
            self.graph.nodes[node]['latest_start'] = (
                self.graph.nodes[node]['latest_finish'] - 
                self.graph.nodes[node]['duration']
            )
            
        # Calculate float and identify critical path
        critical_path = []
        for node in self.graph.nodes:
            total_float = (
                self.graph.nodes[node]['latest_start'] - 
                self.graph.nodes[node]['earliest_start']
            )
            self.graph.nodes[node]['total_float'] = total_float
            if total_float == 0:
                critical_path.append(node)
                
        return {
            'critical_path': critical_path,
            'project_duration': project_end,
            'schedule': {
                node: {
                    'earliest_start': self.graph.nodes[node]['earliest_start'],
                    'latest_start': self.graph.nodes[node]['latest_start'],
                    'earliest_finish': self.graph.nodes[node]['earliest_finish'],
                    'latest_finish': self.graph.nodes[node]['latest_finish'],
                    'total_float': self.graph.nodes[node]['total_float']
                }
                for node in self.graph.nodes
            }
        }
        
    def level_resources(self, tasks: List[Task], resource_capacity: Dict):
        """Optional resource leveling algorithm"""
        # TODO: Implement resource leveling logic
        pass
