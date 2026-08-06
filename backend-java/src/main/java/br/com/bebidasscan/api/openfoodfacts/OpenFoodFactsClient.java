package br.com.bebidasscan.api.openfoodfacts;

import br.com.bebidasscan.api.bebida.dto.BebidaCreateRequest;
import br.com.bebidasscan.api.config.BebidasScanProperties;
import java.util.ArrayList;
import java.util.List;
import java.util.Map;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.stereotype.Service;
import org.springframework.web.client.RestClient;
import org.springframework.web.util.UriComponentsBuilder;

@Service
public class OpenFoodFactsClient {

    private static final Logger LOGGER = LoggerFactory.getLogger(OpenFoodFactsClient.class);
    private static final String PRODUCT_URL = "https://world.openfoodfacts.org/api/v2/product/{codigo}.json";
    private static final String SEARCH_URL = "https://world.openfoodfacts.org/cgi/search.pl";
    private static final String FIELDS = "code,product_name_pt,product_name,generic_name_pt,generic_name,categories_pt,categories,categories_tags,brands,ingredients_text_pt,ingredients_text_with_allergens_pt,ingredients_text,ingredients_text_with_allergens,image_front_url,image_url,nutriscore_grade,nova_group,ecoscore_grade,allergens_pt,allergens,allergens_tags,quantity,packaging_pt,packaging,packaging_tags,countries_pt,countries,countries_tags,nutriments";

    private final BebidasScanProperties properties;
    private final RestClient restClient;
    private final OpenFoodFactsMapper mapper;

    public OpenFoodFactsClient(BebidasScanProperties properties, RestClient.Builder restClientBuilder, OpenFoodFactsMapper mapper) {
        this.properties = properties;
        this.restClient = restClientBuilder.build();
        this.mapper = mapper;
    }

    public BebidaCreateRequest findByBarcode(String barcode) {
        try {
            Map<String, Object> response = restClient.get()
                    .uri(PRODUCT_URL, barcode)
                    .header("User-Agent", properties.openFoodFactsUserAgent())
                    .retrieve()
                    .body(Map.class);
            if (response == null || !Integer.valueOf(1).equals(response.get("status"))) {
                return null;
            }
            Map<String, Object> product = map(response.get("product"));
            if (mapper.productMarkedOutsideBrazil(product)) {
                return null;
            }
            return mapper.toBebidaCreate(product, barcode);
        } catch (RuntimeException exception) {
            LOGGER.warn("open_food_facts_lookup_failed codigoBarras={} errorType={}", barcode, exception.getClass().getSimpleName());
            return null;
        }
    }

    public List<BebidaCreateRequest> searchByName(String term, int limit) {
        if (term == null || term.trim().length() < 2) {
            return List.of();
        }
        try {
            String uri = UriComponentsBuilder.fromHttpUrl(SEARCH_URL)
                    .queryParam("search_terms", term.trim())
                    .queryParam("search_simple", 1)
                    .queryParam("action", "process")
                    .queryParam("json", 1)
                    .queryParam("page_size", limit)
                    .queryParam("fields", FIELDS)
                    .queryParam("tagtype_0", "countries")
                    .queryParam("tag_contains_0", "contains")
                    .queryParam("tag_0", "brazil")
                    .queryParam("lc", "pt")
                    .queryParam("cc", "br")
                    .toUriString();
            Map<String, Object> response = restClient.get()
                    .uri(uri)
                    .header("User-Agent", properties.openFoodFactsUserAgent())
                    .retrieve()
                    .body(Map.class);
            List<?> products = response == null || !(response.get("products") instanceof List<?> list) ? List.of() : list;
            List<BebidaCreateRequest> drinks = new ArrayList<>();
            for (Object item : products) {
                Map<String, Object> product = map(item);
                if (mapper.productMarkedOutsideBrazil(product)) {
                    continue;
                }
                BebidaCreateRequest drink = mapper.toBebidaCreate(product, null);
                if (drink != null) {
                    drinks.add(drink);
                }
                if (drinks.size() >= limit) {
                    break;
                }
            }
            return drinks;
        } catch (RuntimeException exception) {
            LOGGER.warn("open_food_facts_search_failed termo={} errorType={}", term, exception.getClass().getSimpleName());
            return List.of();
        }
    }

    @SuppressWarnings("unchecked")
    private static Map<String, Object> map(Object value) {
        return value instanceof Map<?, ?> ? (Map<String, Object>) value : Map.of();
    }
}
