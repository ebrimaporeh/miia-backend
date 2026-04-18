# apps/core/pagination.py
from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response
from collections import OrderedDict

class CustomPageNumberPagination(PageNumberPagination):
    """
    Custom pagination class that provides detailed pagination metadata.
    
    Features:
    - Configurable page size (default: 10)
    - Page size query parameter: `page_size`
    - Max page size limit (default: 100)
    - Returns last_page, next_page, previous_page numbers
    - Returns start_index and end_index for the current page
    """
    page_size = 10
    page_size_query_param = 'page_size'
    max_page_size = 100
    page_query_param = 'page'
    
    def get_paginated_response(self, data):
        """
        Return paginated response with enhanced metadata.
        
        Response structure:
        {
            "count": 100,
            "page": 1,
            "page_size": 10,
            "total_pages": 10,
            "next_page": 2,
            "previous_page": null,
            "first_page": 1,
            "last_page": 10,
            "start_index": 1,
            "end_index": 10,
            "has_next": true,
            "has_previous": false,
            "results": [...]
        }
        """
        page = self.page
        total_pages = page.paginator.num_pages
        current_page = page.number
        page_size = self.get_page_size(self.request)
        
        # Calculate start and end indices
        start_index = (current_page - 1) * page_size + 1
        end_index = min(current_page * page_size, page.paginator.count)
        
        return Response(OrderedDict([
            ('count', page.paginator.count),
            ('page', current_page),
            ('page_size', page_size),
            ('total_pages', total_pages),
            ('next_page', current_page + 1 if page.has_next() else None),
            ('previous_page', current_page - 1 if page.has_previous() else None),
            ('first_page', 1),
            ('last_page', total_pages),
            ('start_index', start_index if page.paginator.count > 0 else 0),
            ('end_index', end_index),
            ('has_next', page.has_next()),
            ('has_previous', page.has_previous()),
            ('results', data)
        ]))
    
    def get_paginated_response_schema(self, view):
        """
        Generate OpenAPI schema for paginated response.
        """
        # Try to get the serializer class from the view
        try:
            # For viewsets, get the serializer class
            if hasattr(view, 'get_serializer'):
                serializer = view.get_serializer()
                if hasattr(serializer, 'get_serializer_class'):
                    serializer_class = serializer.get_serializer_class()
                else:
                    serializer_class = serializer.__class__
            elif hasattr(view, 'serializer_class'):
                serializer_class = view.serializer_class
            else:
                # Fallback to a generic object schema
                return {
                    'type': 'object',
                    'properties': {
                        'count': {'type': 'integer', 'example': 100},
                        'page': {'type': 'integer', 'example': 1},
                        'page_size': {'type': 'integer', 'example': 10},
                        'total_pages': {'type': 'integer', 'example': 10},
                        'next_page': {'type': 'integer', 'example': 2, 'nullable': True},
                        'previous_page': {'type': 'integer', 'example': None, 'nullable': True},
                        'first_page': {'type': 'integer', 'example': 1},
                        'last_page': {'type': 'integer', 'example': 10},
                        'start_index': {'type': 'integer', 'example': 1},
                        'end_index': {'type': 'integer', 'example': 10},
                        'has_next': {'type': 'boolean', 'example': True},
                        'has_previous': {'type': 'boolean', 'example': False},
                        'results': {
                            'type': 'array',
                            'items': {'type': 'object'}
                        }
                    }
                }
        except Exception:
            # Fallback to a generic object schema
            return {
                'type': 'object',
                'properties': {
                    'count': {'type': 'integer', 'example': 100},
                    'page': {'type': 'integer', 'example': 1},
                    'page_size': {'type': 'integer', 'example': 10},
                    'total_pages': {'type': 'integer', 'example': 10},
                    'next_page': {'type': 'integer', 'example': 2, 'nullable': True},
                    'previous_page': {'type': 'integer', 'example': None, 'nullable': True},
                    'first_page': {'type': 'integer', 'example': 1},
                    'last_page': {'type': 'integer', 'example': 10},
                    'start_index': {'type': 'integer', 'example': 1},
                    'end_index': {'type': 'integer', 'example': 10},
                    'has_next': {'type': 'boolean', 'example': True},
                    'has_previous': {'type': 'boolean', 'example': False},
                    'results': {
                        'type': 'array',
                        'items': {'type': 'object'}
                    }
                }
            }
        
        # Build the schema with the proper results items
        return {
            'type': 'object',
            'properties': {
                'count': {'type': 'integer', 'example': 100},
                'page': {'type': 'integer', 'example': 1},
                'page_size': {'type': 'integer', 'example': 10},
                'total_pages': {'type': 'integer', 'example': 10},
                'next_page': {'type': 'integer', 'example': 2, 'nullable': True},
                'previous_page': {'type': 'integer', 'example': None, 'nullable': True},
                'first_page': {'type': 'integer', 'example': 1},
                'last_page': {'type': 'integer', 'example': 10},
                'start_index': {'type': 'integer', 'example': 1},
                'end_index': {'type': 'integer', 'example': 10},
                'has_next': {'type': 'boolean', 'example': True},
                'has_previous': {'type': 'boolean', 'example': False},
                'results': {
                    'type': 'array',
                    'items': serializer_class().to_representation if hasattr(serializer_class, 'to_representation') else {'type': 'object'}
                }
            }
        }


class SmallPagination(CustomPageNumberPagination):
    """Pagination with small page size (5 items per page)"""
    page_size = 5
    max_page_size = 20


class LargePagination(CustomPageNumberPagination):
    """Pagination with large page size (25 items per page)"""
    page_size = 25
    max_page_size = 200


class MobilePagination(CustomPageNumberPagination):
    """Pagination optimized for mobile devices (15 items per page)"""
    page_size = 15
    max_page_size = 50