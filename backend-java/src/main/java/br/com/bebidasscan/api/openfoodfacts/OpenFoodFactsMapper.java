package br.com.bebidasscan.api.openfoodfacts;

import br.com.bebidasscan.api.bebida.dto.BebidaCreateRequest;
import java.math.BigDecimal;
import java.util.List;
import java.util.Map;
import org.springframework.stereotype.Component;

@Component
public class OpenFoodFactsMapper {

    public BebidaCreateRequest toBebidaCreate(Map<String, Object> product, String barcode) {
        String name = firstText(product, "product_name_pt", "product_name", "generic_name_pt", "generic_name");
        if (name == null) {
            return null;
        }
        String categories = String.join(" ", tags(product.get("categories_tags"))).toLowerCase();
        String type = classifyType(categories);
        if (type == null) {
            return null;
        }
        Map<String, Object> nutriments = map(product.get("nutriments"));
        BigDecimal alcohol = decimal(
                firstObject(nutriments, "alcohol_100g", "alcohol", "alcohol_value")
        );
        return new BebidaCreateRequest(
                limit(name, 200),
                limit(text(product.get("brands")), 150),
                type,
                validBarcode(barcode == null ? text(product.get("code")) : barcode),
                alcohol,
                firstText(product, "ingredients_text_pt", "ingredients_text_with_allergens_pt", "ingredients_text", "ingredients_text_with_allergens"),
                firstText(product, "image_front_url", "image_url"),
                limit(text(product.get("nutriscore_grade")), 10),
                integer(product.get("nova_group")),
                limit(text(product.get("ecoscore_grade")), 30),
                firstText(product, "allergens_pt", "allergens"),
                firstText(product, "categories_pt", "categories"),
                limit(text(product.get("quantity")), 80),
                firstText(product, "packaging_pt", "packaging"),
                firstText(product, "countries_pt", "countries"),
                null, null, null, null, null, null, null, null, null, null, null
        );
    }

    public boolean productMarkedOutsideBrazil(Map<String, Object> product) {
        List<String> tags = tags(product.get("countries_tags"));
        return !tags.isEmpty() && tags.stream().noneMatch("en:brazil"::equalsIgnoreCase);
    }

    private static String classifyType(String categories) {
        if (categories == null || !categories.matches(".*(beverage|bebida|drink|alcohol|cerveja|beer|wine|vinho|spirit|liquor|juice|suco|water|agua|soda|refrigerante|soft-drink|energy-drink|energetico|tea|cha|coffee|cafe).*")) {
            return null;
        }
        if (categories.contains("beer") || categories.contains("cerveja")) return "cerveja";
        if (categories.contains("wine") || categories.contains("vinho")) return "vinho";
        if (categories.contains("spirit") || categories.contains("liquor")) return "destilado";
        if (categories.contains("energy-drink") || categories.contains("energetico")) return "energetico";
        if (categories.contains("soda") || categories.contains("soft-drink") || categories.contains("refrigerante")) return "refrigerante";
        if (categories.contains("juice") || categories.contains("suco")) return "suco";
        if (categories.contains("water") || categories.contains("agua")) return "agua";
        if (categories.contains("tea") || categories.contains("cha")) return "cha";
        if (categories.contains("coffee") || categories.contains("cafe")) return "cafe";
        return "bebida";
    }

    private static String firstText(Map<String, Object> source, String... keys) {
        for (String key : keys) {
            String value = text(source.get(key));
            if (value != null) return value;
        }
        return null;
    }

    private static Object firstObject(Map<String, Object> source, String... keys) {
        for (String key : keys) {
            Object value = source.get(key);
            if (value != null) return value;
        }
        return null;
    }

    private static String text(Object value) {
        if (value == null) return null;
        String text = value.toString().trim();
        return text.isBlank() ? null : text;
    }

    private static String limit(String value, int limit) {
        return value == null ? null : value.substring(0, Math.min(value.length(), limit));
    }

    private static String validBarcode(String value) {
        return value != null && value.length() >= 6 && value.length() <= 80 ? value : null;
    }

    private static Integer integer(Object value) {
        try {
            return value == null ? null : Integer.valueOf(value.toString());
        } catch (NumberFormatException exception) {
            return null;
        }
    }

    private static BigDecimal decimal(Object value) {
        try {
            return value == null ? null : new BigDecimal(value.toString());
        } catch (NumberFormatException exception) {
            return null;
        }
    }

    @SuppressWarnings("unchecked")
    private static Map<String, Object> map(Object value) {
        return value instanceof Map<?, ?> ? (Map<String, Object>) value : Map.of();
    }

    private static List<String> tags(Object value) {
        if (!(value instanceof List<?> list)) {
            return List.of();
        }
        return list.stream().map(String::valueOf).map(String::trim).filter(item -> !item.isBlank()).toList();
    }
}
