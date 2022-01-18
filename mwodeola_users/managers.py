from django.contrib.auth.models import BaseUserManager


class MwodeolaUserManager(BaseUserManager):

    def create_user(self, user_name, email, phone_number, password):
        if not email:
            raise ValueError("Users Must Have an email address.")
        if not user_name:
            raise ValueError("Users Must Have an name.")
        if not phone_number:
            raise ValueError("Users Must Have an phone number.")
        if not password:
            raise ValueError("Users Must Have an password.")

        user = self.model(
            email=self.normalize_email(email),
            user_name=user_name,
            phone_number=phone_number,
            # nickname=nickname,
        )
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, user_name, email, phone_number, password):
        if password is None:
            raise TypeError("Superusers must have a password.")

        user = self.create_user(user_name, email, phone_number, password)
        user.is_superuser = True
        user.is_staff = True
        user.is_active = True
        user.save()

        return user
