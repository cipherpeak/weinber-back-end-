from .models import Note
from rest_framework import serializers
from authapp.models import Employee
from datetime import datetime
import pytz

class NoteSerializer(serializers.ModelSerializer):
    
    class Meta:
        model = Note
        fields = [
            'id',
            'title',
            'date',
        ]
    
    def validate_title(self, value):
        """Validate title field"""
        if not value.strip():
            raise serializers.ValidationError("Title cannot be empty")
        if len(value) > 200:
            raise serializers.ValidationError("Title cannot exceed 200 characters")
        return value.strip()
    
    
    def validate_date(self, value):
        """Validate date field"""
        if not value.strip():
            raise serializers.ValidationError("Date cannot be empty")
        
        # Try to parse the date to ensure it's valid
        date_formats = [
            '%d %B %Y',      # "19 December 2024"
            '%d-%b-%Y',      # "19-Dec-2024"
            '%Y-%m-%d',      # "2024-12-19"
            '%d/%m/%Y',      # "19/12/2024"
            '%m/%d/%Y',      # "12/19/2024"
            '%B %d, %Y',     # "December 19, 2024"
            '%d %b %Y',      # "19 Dec 2024"
        ]
        
        for date_format in date_formats:
            try:
                datetime.strptime(value.strip(), date_format)
                return value.strip()
            except ValueError:
                continue
        
        raise serializers.ValidationError(
            "Please enter date in a valid format (e.g., '19 December 2024', '2024-12-19')"
        )
    


class NoteCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Note
        fields = ['title', 'description', 'date']
    
    def validate_title(self, value):
        if not value.strip():
            raise serializers.ValidationError("Title is required")
        if len(value) > 200:
            raise serializers.ValidationError("Title cannot exceed 200 characters")
        return value.strip()
    
    def validate_description(self, value):
        if not value.strip():
            raise serializers.ValidationError("Description is required")
        return value.strip()
    
    def validate_date(self, value):
        if not value.strip():
            raise serializers.ValidationError("Date is required")
        return value.strip()


class NoteDetailSerializer(NoteSerializer):
    class Meta(NoteSerializer.Meta):
        fields = NoteSerializer.Meta.fields + ['description']