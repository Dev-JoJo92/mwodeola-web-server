from rest_framework import serializers, status


class TestSerializer(serializers.Serializer):
    results = {}
    error_messages = {}
    error_status = 400

    email = serializers.EmailField(max_length=20)

    def is_valid(self, raise_exception=False):
        if not super().is_valid(raise_exception):
            return False

        email = self.validated_data['email']

        if email.__contains__('@naver.'):
            self.error_messages = {'error_code': 'can not Naver'}
            self.error_status = status.HTTP_403_FORBIDDEN
            return False

        self.results['code'] = 'success'
        self.results['data'] = email

        return True

    def validate(self, attrs):
        super().validate(attrs)
        return attrs

    def create(self, validated_data):
        pass

    def update(self, instance, validated_data):
        pass
