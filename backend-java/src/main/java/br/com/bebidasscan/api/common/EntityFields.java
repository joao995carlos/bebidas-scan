package br.com.bebidasscan.api.common;

import java.lang.reflect.Field;

public final class EntityFields {

    private EntityFields() {
    }

    public static Object get(Object target, String fieldName) {
        try {
            Field field = findField(target.getClass(), fieldName);
            field.setAccessible(true);
            return field.get(target);
        } catch (ReflectiveOperationException exception) {
            throw new IllegalStateException("Campo inacessivel: " + fieldName, exception);
        }
    }

    @SuppressWarnings("unchecked")
    public static <T> T get(Object target, String fieldName, Class<T> type) {
        Object value = get(target, fieldName);
        return value == null ? null : (T) value;
    }

    public static void set(Object target, String fieldName, Object value) {
        try {
            Field field = findField(target.getClass(), fieldName);
            field.setAccessible(true);
            field.set(target, value);
        } catch (ReflectiveOperationException exception) {
            throw new IllegalStateException("Campo inacessivel: " + fieldName, exception);
        }
    }

    private static Field findField(Class<?> type, String fieldName) throws NoSuchFieldException {
        Class<?> current = type;
        while (current != null) {
            try {
                return current.getDeclaredField(fieldName);
            } catch (NoSuchFieldException ignored) {
                current = current.getSuperclass();
            }
        }
        throw new NoSuchFieldException(fieldName);
    }
}
