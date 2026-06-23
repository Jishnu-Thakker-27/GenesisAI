import re

class CanonicalNamingEngine:
    @staticmethod
    def sanitize(text: str) -> str:
        """Removes all non-alphanumeric characters and converts whitespace/hyphens to spaces."""
        if not text:
            return ""
        # Replace punctuation/special chars (except spaces/hyphens/underscores) with nothing
        cleaned = re.sub(r"[^\w\s\-]", "", text)
        # Standardize separators to single spaces
        cleaned = re.sub(r"[\s\-_]+", " ", cleaned)
        return cleaned.strip()

    @staticmethod
    def to_pascal_case(text: str) -> str:
        """Converts strings to PascalCase (e.g., 'gym class booking' -> 'GymClassBooking')."""
        if text and " " not in text and "_" not in text and "-" not in text:
            text = re.sub(r"(?<!^)(?=[A-Z])", " ", text)
        sanitized = CanonicalNamingEngine.sanitize(text)
        if not sanitized:
            return ""
        words = sanitized.split(" ")
        return "".join(word.capitalize() for word in words)

    @staticmethod
    def to_snake_case(text: str) -> str:
        """Converts strings to snake_case (e.g., 'Gym Class Booking' -> 'gym_class_booking')."""
        sanitized = CanonicalNamingEngine.sanitize(text)
        if not sanitized:
            return ""
        if " " not in sanitized:
            sanitized = re.sub(r"(?<!^)(?=[A-Z])", "_", sanitized)
        words = sanitized.split(" ")
        return "_".join(word.lower() for word in words if word)

    @staticmethod
    def to_kebab_case(text: str) -> str:
        """Converts strings to kebab-case (e.g., 'Gym Class Booking' -> 'gym-class-booking')."""
        if text and " " not in text and "_" not in text and "-" not in text:
            text = re.sub(r"(?<!^)(?=[A-Z])", " ", text)
        sanitized = CanonicalNamingEngine.sanitize(text)
        if not sanitized:
            return ""
        words = sanitized.split(" ")
        return "-".join(word.lower() for word in words if word)

    @staticmethod
    def sanitize_endpoint_path(path: str) -> str:
        """Enforces clean API routes (e.g. '/api/v1/gym-class-booking' or '/bookings')."""
        if not path:
            return "/"
        # Split route by '/'
        parts = path.strip().split("/")
        sanitized_parts = []
        for part in parts:
            if not part:
                continue
            # Handle path variables like {id} or {member_id}
            if part.startswith("{") and part.endswith("}"):
                variable = part[1:-1]
                sanitized_parts.append(f"{{{CanonicalNamingEngine.to_snake_case(variable)}}}")
            else:
                sanitized_parts.append(CanonicalNamingEngine.to_kebab_case(part))
        prefix = "/" if path.startswith("/") else ""
        return prefix + "/".join(sanitized_parts)
