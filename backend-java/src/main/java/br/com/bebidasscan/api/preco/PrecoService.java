package br.com.bebidasscan.api.preco;

import br.com.bebidasscan.api.bebida.Bebida;
import br.com.bebidasscan.api.bebida.BebidaRepository;
import br.com.bebidasscan.api.common.ApiException;
import br.com.bebidasscan.api.common.EntityFields;
import br.com.bebidasscan.api.preco.dto.PrecoCreateRequest;
import br.com.bebidasscan.api.preco.dto.PrecoResponse;
import br.com.bebidasscan.api.usuario.Usuario;
import java.util.Comparator;
import java.util.List;
import org.springframework.http.HttpStatus;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

@Service
public class PrecoService {

    private final PrecoRepository precoRepository;
    private final BebidaRepository bebidaRepository;
    private final PrecoMapper mapper;

    public PrecoService(PrecoRepository precoRepository, BebidaRepository bebidaRepository, PrecoMapper mapper) {
        this.precoRepository = precoRepository;
        this.bebidaRepository = bebidaRepository;
        this.mapper = mapper;
    }

    @Transactional
    public PrecoResponse create(PrecoCreateRequest request, Usuario usuario) {
        Bebida bebida = bebidaRepository.findById(request.idBebida())
                .orElseThrow(() -> new ApiException(HttpStatus.NOT_FOUND, "Bebida nao encontrada"));
        Preco preco = new Preco();
        EntityFields.set(preco, "usuario", usuario);
        EntityFields.set(preco, "bebida", bebida);
        EntityFields.set(preco, "mercado", clean(request.mercado()));
        EntityFields.set(preco, "cidade", clean(request.cidade()));
        EntityFields.set(preco, "estado", clean(request.estado()) == null ? null : clean(request.estado()).toUpperCase());
        EntityFields.set(preco, "valor", request.valor());
        return mapper.toResponse(precoRepository.save(preco));
    }

    public List<PrecoResponse> listByBebida(Integer bebidaId) {
        Bebida bebida = bebidaRepository.findById(bebidaId)
                .orElseThrow(() -> new ApiException(HttpStatus.NOT_FOUND, "Bebida nao encontrada"));
        return precoRepository.findByBebidaOrderByDataRegistroDesc(bebida).stream()
                .sorted(Comparator.comparing(item -> String.valueOf(EntityFields.get(item, "dataRegistro")), Comparator.reverseOrder()))
                .limit(50)
                .map(mapper::toResponse)
                .toList();
    }

    private String clean(String value) {
        if (value == null) return null;
        String cleaned = value.trim();
        return cleaned.isBlank() ? null : cleaned;
    }
}
