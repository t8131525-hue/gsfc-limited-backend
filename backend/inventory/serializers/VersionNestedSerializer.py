from rest_framework import serializers
from ..models import Version
from .ProductGradeSerializer import ProductGradeSerializer
from .ParameterDefinitionSerializer import ParameterDefinitionSerializer

class VersionNestedSerializer(serializers.ModelSerializer):
    """
    A read-only serializer to display version details nested within a Product.
    """
    # ✅ 1. Change this field to a SerializerMethodField.
    parameters = serializers.SerializerMethodField()
    
    # Nests the grades that are on the version (this part works correctly)
    grades = ProductGradeSerializer(many=True, read_only=True)

    class Meta:
        model = Version
        fields = [
            'id', 'version_name', 'status', 'is_active', 
            'description', 'parameters', 'grades',
            'created_at', 'locked_at', 'activated_at'
        ]


    # ✅ 2. Add this method to explicitly define how to get the parameters.
    def get_parameters(self, obj):
        """
        Explicitly fetches and serializes the parameters for the version.
        This leverages the 'prefetch_related' from the ViewSet for efficiency.
        """
        # 'obj' is the Version instance. The '.parameters' here refers to
        # the GenericRelation field on the Version model.
        parameters = obj.parameters.all()
        
        # We pass the 'request' context, which is good practice for serializers
        # that might need it for things like generating full URLs for hyperlinks.
        request = self.context.get('request')
        return ParameterDefinitionSerializer(parameters, many=True, context={'request': request}).data