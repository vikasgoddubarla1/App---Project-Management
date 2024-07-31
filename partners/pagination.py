from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response
from rest_framework import response


class CustomPagination(PageNumberPagination):
    page_size = 10
    max_page_size = 10000
    
    def get_page_size(self, request):
        if 'page_size' in request.query_params:
            try:
                return int(request.query_params['page_size'])
            except ValueError:
                pass
        return self.page_size
    
    def get_paginated_response(self, data):
        return Response(data)

    
class LocationFieldsPagination(PageNumberPagination):
   page_size = 30
   
   def get_paginated_response(self, data):
       return response.Response({
           'locationFields': data,
           'paginationDetails': {
               'current_page': self.page.number,
               'number_of_pages': self.page.paginator.num_pages,
               'current_page_items': len(data),
               'total_items': self.page.paginator.count,
               'next_page': self.get_next_link(),
               'previous_page': self.get_previous_link(),
           }
       })