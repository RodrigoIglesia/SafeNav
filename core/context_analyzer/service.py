# core/context_analyzer/service.py
"""
Context Analyzer
------------------------------------
Implements the IContextService interface.
"""

from domain.dto.routes import RouteCandidates, RouteScores

from interfaces.i_context_service import IContextService
from interfaces.i_open_data_access import IOpenDataAccess

class ContextAnalyzer(IContextService):
    def __init__(self, open_data_access: IOpenDataAccess):
        self.open_data_access = open_data_access

    def evaluate_routes(self, routes: RouteCandidates) -> RouteScores:
        """
        Evaluates route candidates for the ones calculated by RE
        """
        pass