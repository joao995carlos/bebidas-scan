package br.com.bebidasscan.api.bebida;

import br.com.bebidasscan.api.bebida.dto.BebidaCreateRequest;
import br.com.bebidasscan.api.bebida.dto.BebidaResponse;
import br.com.bebidasscan.api.bebida.dto.BebidaUpdateRequest;
import br.com.bebidasscan.api.bebida.dto.CachacaRequest;
import br.com.bebidasscan.api.common.ApiException;
import br.com.bebidasscan.api.common.EntityFields;
import br.com.bebidasscan.api.openfoodfacts.OpenFoodFactsClient;
import br.com.bebidasscan.api.usuario.Usuario;
import java.text.Normalizer;
import java.util.ArrayList;
import java.util.LinkedHashSet;
import java.util.List;
import java.util.Set;
import org.springframework.dao.DataIntegrityViolationException;
import org.springframework.http.HttpStatus;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

@Service
public class BebidaService {

    private static final Set<String> BRAZIL_TERMS = Set.of("brazil", "brasil");

    private final BebidaRepository bebidaRepository;
    private final CachacaRepository cachacaRepository;
    private final BebidaMapper mapper;
    private final TipoBebidaService tipoBebidaService;
    private final OpenFoodFactsClient openFoodFactsClient;

    public BebidaService(
            BebidaRepository bebidaRepository,
            CachacaRepository cachacaRepository,
            BebidaMapper mapper,
            TipoBebidaService tipoBebidaService,
            OpenFoodFactsClient openFoodFactsClient
    ) {
        this.bebidaRepository = bebidaRepository;
        this.cachacaRepository = cachacaRepository;
        this.mapper = mapper;
        this.tipoBebidaService = tipoBebidaService;
        this.openFoodFactsClient = openFoodFactsClient;
    }

    @Transactional
    public BebidaResponse create(BebidaCreateRequest request, Usuario usuario) {
        if (hasText(request.codigoBarras()) && bebidaRepository.findByCodigoBarras(request.codigoBarras().trim()).isPresent()) {
            throw new ApiException(HttpStatus.BAD_REQUEST, "Codigo de barras ja cadastrado");
        }
        Bebida bebida = new Bebida();
        applyCreateFields(bebida, request);
        EntityFields.set(bebida, "origemDados", "usuario");
        EntityFields.set(bebida, "criadoPor", usuario);
        bebida = saveHandlingBarcodeConflict(bebida);
        saveCachaca(bebida, cachacaFromCreate(request));
        return mapper.toResponse(saveHandlingBarcodeConflict(bebida));
    }

    @Transactional
    public BebidaResponse update(Integer bebidaId, BebidaUpdateRequest request, Usuario usuario) {
        Bebida bebida = bebidaRepository.findById(bebidaId)
                .orElseThrow(() -> new ApiException(HttpStatus.NOT_FOUND, "Bebida nao encontrada"));
        Usuario owner = EntityFields.get(bebida, "criadoPor", Usuario.class);
        if ((owner == null || !owner.equals(usuario)) && !isAdmin(usuario)) {
            throw new ApiException(HttpStatus.FORBIDDEN, "Voce nao pode editar esta bebida");
        }
        if (hasText(request.codigoBarras()) && !request.codigoBarras().trim().equals(bebida.getCodigoBarras())) {
            bebidaRepository.findByCodigoBarras(request.codigoBarras().trim()).ifPresent(existing -> {
                throw new ApiException(HttpStatus.BAD_REQUEST, "Codigo de barras ja cadastrado");
            });
        }
        applyUpdateFields(bebida, request);
        EntityFields.set(bebida, "origemDados", "usuario");
        saveCachaca(bebida, cachacaFromUpdate(request));
        return mapper.toResponse(saveHandlingBarcodeConflict(bebida));
    }

    @Transactional
    public BebidaResponse findByBarcode(String barcode) {
        String code = barcode == null ? "" : barcode.trim();
        Bebida local = bebidaRepository.findByCodigoBarras(code).orElse(null);
        if (local != null && isExternalFromBrazil(local)) {
            return mapper.toResponse(local);
        }
        BebidaCreateRequest external = openFoodFactsClient.findByBarcode(code);
        if (external == null) {
            throw new ApiException(HttpStatus.NOT_FOUND, "Bebida nao encontrada");
        }
        Bebida bebida = new Bebida();
        applyCreateFields(bebida, external);
        EntityFields.set(bebida, "origemDados", "open_food_facts");
        try {
            bebida = bebidaRepository.save(bebida);
            saveCachaca(bebida, cachacaFromCreate(external));
            return mapper.toResponse(bebidaRepository.save(bebida));
        } catch (DataIntegrityViolationException exception) {
            return bebidaRepository.findByCodigoBarras(code)
                    .map(mapper::toResponse)
                    .orElseThrow(() -> new ApiException(HttpStatus.CONFLICT, "Conflito ao salvar bebida"));
        }
    }

    @Transactional
    public List<BebidaResponse> searchByName(String query) {
        String term = query == null ? "" : query.trim();
        List<Bebida> drinks = localSearch(term, 25);
        if (drinks.size() < 10) {
            Set<String> seenCodes = new LinkedHashSet<>();
            drinks.stream().map(Bebida::getCodigoBarras).filter(this::hasText).forEach(seenCodes::add);
            for (String externalTerm : externalSearchTerms(term)) {
                for (BebidaCreateRequest external : openFoodFactsClient.searchByName(externalTerm, 10)) {
                    if (hasText(external.codigoBarras()) && seenCodes.contains(external.codigoBarras())) {
                        continue;
                    }
                    Bebida bebida = hasText(external.codigoBarras())
                            ? bebidaRepository.findByCodigoBarras(external.codigoBarras()).orElse(null)
                            : null;
                    if (bebida == null) {
                        bebida = new Bebida();
                        applyCreateFields(bebida, external);
                        EntityFields.set(bebida, "origemDados", "open_food_facts");
                        try {
                            bebida = bebidaRepository.save(bebida);
                            saveCachaca(bebida, cachacaFromCreate(external));
                            bebida = bebidaRepository.save(bebida);
                        } catch (DataIntegrityViolationException exception) {
                            continue;
                        }
                    }
                    boolean alreadyListed = false;
                    for (Bebida item : drinks) {
                        if (item.getIdBebida().equals(bebida.getIdBebida())) {
                            alreadyListed = true;
                            break;
                        }
                    }
                    if (isExternalFromBrazil(bebida) && !alreadyListed) {
                        drinks.add(bebida);
                    }
                    if (drinks.size() >= 25) {
                        return drinks.stream().limit(25).map(mapper::toResponse).toList();
                    }
                }
            }
        }
        return drinks.stream().limit(25).map(mapper::toResponse).toList();
    }

    private Bebida saveHandlingBarcodeConflict(Bebida bebida) {
        try {
            return bebidaRepository.save(bebida);
        } catch (DataIntegrityViolationException exception) {
            throw new ApiException(HttpStatus.BAD_REQUEST, "Codigo de barras ja cadastrado");
        }
    }

    private void applyCreateFields(Bebida bebida, BebidaCreateRequest request) {
        setIfPresent(bebida, "nome", request.nome());
        setIfPresent(bebida, "marca", clean(request.marca()));
        setIfPresent(bebida, "tipo", request.tipo());
        setIfPresent(bebida, "codigoBarras", clean(request.codigoBarras()));
        setIfPresent(bebida, "teorAlcoolico", request.teorAlcoolico());
        setIfPresent(bebida, "ingredientes", clean(request.ingredientes()));
        setIfPresent(bebida, "imagemUrl", clean(request.imagemUrl()));
        setIfPresent(bebida, "nutriScore", clean(request.nutriScore()));
        setIfPresent(bebida, "novaGrupo", request.novaGrupo());
        setIfPresent(bebida, "ecoScore", clean(request.ecoScore()));
        setIfPresent(bebida, "alergenos", clean(request.alergenos()));
        setIfPresent(bebida, "categorias", clean(request.categorias()));
        setIfPresent(bebida, "quantidade", clean(request.quantidade()));
        setIfPresent(bebida, "embalagem", clean(request.embalagem()));
        setIfPresent(bebida, "paises", clean(request.paises()));
    }

    private void applyUpdateFields(Bebida bebida, BebidaUpdateRequest request) {
        setIfPresent(bebida, "nome", clean(request.nome()));
        setIfPresent(bebida, "marca", clean(request.marca()));
        setIfPresent(bebida, "tipo", clean(request.tipo()));
        setIfPresent(bebida, "codigoBarras", clean(request.codigoBarras()));
        setIfPresent(bebida, "teorAlcoolico", request.teorAlcoolico());
        setIfPresent(bebida, "ingredientes", clean(request.ingredientes()));
        setIfPresent(bebida, "imagemUrl", clean(request.imagemUrl()));
        setIfPresent(bebida, "nutriScore", clean(request.nutriScore()));
        setIfPresent(bebida, "novaGrupo", request.novaGrupo());
        setIfPresent(bebida, "ecoScore", clean(request.ecoScore()));
        setIfPresent(bebida, "alergenos", clean(request.alergenos()));
        setIfPresent(bebida, "categorias", clean(request.categorias()));
        setIfPresent(bebida, "quantidade", clean(request.quantidade()));
        setIfPresent(bebida, "embalagem", clean(request.embalagem()));
        setIfPresent(bebida, "paises", clean(request.paises()));
    }

    private void saveCachaca(Bebida bebida, CachacaRequest request) {
        if (!tipoBebidaService.isCachacaOrAguardente(EntityFields.get(bebida, "tipo", String.class)) || request == null) {
            return;
        }
        Cachaca cachaca = cachacaRepository.findAll().stream()
                .filter(item -> bebida.equals(EntityFields.get(item, "bebida", Bebida.class)))
                .findFirst()
                .orElseGet(Cachaca::new);
        EntityFields.set(cachaca, "bebida", bebida);
        setIfPresent(cachaca, "volumeMl", request.volumeMl());
        setIfPresent(cachaca, "classificacao", clean(request.classificacao()));
        setIfPresent(cachaca, "madeira", clean(request.madeira()));
        setIfPresent(cachaca, "tempoEnvelhecimentoMeses", request.tempoEnvelhecimentoMeses());
        setIfPresent(cachaca, "cidadeOrigem", clean(request.cidadeOrigem()));
        setIfPresent(cachaca, "estadoOrigem", clean(request.estadoOrigem()) == null ? null : clean(request.estadoOrigem()).toUpperCase());
        setIfPresent(cachaca, "regiaoOrigem", clean(request.regiaoOrigem()));
        setIfPresent(cachaca, "alambique", clean(request.alambique()));
        setIfPresent(cachaca, "produtor", clean(request.produtor()));
        setIfPresent(cachaca, "lote", clean(request.lote()));
        cachacaRepository.save(cachaca);
        EntityFields.set(bebida, "cachaca", cachaca);
    }

    private List<Bebida> localSearch(String term, int limit) {
        String normalizedTerm = normalizeSearch(term);
        List<Bebida> results = new ArrayList<>();
        for (Bebida bebida : bebidaRepository.findAll()) {
            if (!isExternalFromBrazil(bebida)) {
                continue;
            }
            String text = String.join(" ",
                    value(bebida.getNome()),
                    value(EntityFields.get(bebida, "marca")),
                    value(EntityFields.get(bebida, "tipo")),
                    value(EntityFields.get(bebida, "categorias")),
                    value(EntityFields.get(bebida, "ingredientes"))
            );
            if (normalizeSearch(text).contains(normalizedTerm)) {
                results.add(bebida);
            }
            if (results.size() >= limit) {
                break;
            }
        }
        return results;
    }

    private List<String> externalSearchTerms(String term) {
        String normalized = normalizeSearch(term);
        List<String> terms = new ArrayList<>();
        terms.add(term);
        switch (normalized) {
            case "agua" -> terms.addAll(List.of("agua", "water"));
            case "coca" -> terms.addAll(List.of("coca cola", "cola"));
            case "refrigerante" -> terms.addAll(List.of("soda", "soft drink"));
            case "cerveja" -> terms.add("beer");
            case "suco" -> terms.add("juice");
            case "energetico" -> terms.add("energy drink");
            default -> {
            }
        }
        return terms.stream().filter(this::hasText).distinct().toList();
    }

    private boolean isExternalFromBrazil(Bebida bebida) {
        String origin = EntityFields.get(bebida, "origemDados", String.class);
        if (!"open_food_facts".equals(origin)) {
            return true;
        }
        String countries = normalizeSearch(EntityFields.get(bebida, "paises", String.class));
        return BRAZIL_TERMS.stream().anyMatch(countries::contains);
    }

    private boolean isAdmin(Usuario usuario) {
        return "admin".equals(EntityFields.get(usuario, "tipoUsuario", String.class));
    }

    private CachacaRequest cachacaFromCreate(BebidaCreateRequest request) {
        if (request.cachaca() != null) {
            return request.cachaca();
        }
        return new CachacaRequest(request.volumeMl(), request.classificacao(), request.madeira(), request.tempoEnvelhecimentoMeses(),
                request.cidadeOrigem(), request.estadoOrigem(), request.regiaoOrigem(), request.alambique(), request.produtor(), request.lote());
    }

    private CachacaRequest cachacaFromUpdate(BebidaUpdateRequest request) {
        if (request.cachaca() != null) {
            return request.cachaca();
        }
        return new CachacaRequest(request.volumeMl(), request.classificacao(), request.madeira(), request.tempoEnvelhecimentoMeses(),
                request.cidadeOrigem(), request.estadoOrigem(), request.regiaoOrigem(), request.alambique(), request.produtor(), request.lote());
    }

    private void setIfPresent(Object target, String field, Object value) {
        if (value != null) {
            EntityFields.set(target, field, value);
        }
    }

    private String clean(String value) {
        if (value == null) return null;
        String cleaned = value.trim();
        return cleaned.isBlank() ? null : cleaned;
    }

    private boolean hasText(String value) {
        return value != null && !value.trim().isBlank();
    }

    private static String normalizeSearch(String value) {
        return Normalizer.normalize(value == null ? "" : value, Normalizer.Form.NFD)
                .replaceAll("\\p{M}", "")
                .toLowerCase()
                .trim();
    }

    private static String value(Object value) {
        return value == null ? "" : value.toString();
    }
}
