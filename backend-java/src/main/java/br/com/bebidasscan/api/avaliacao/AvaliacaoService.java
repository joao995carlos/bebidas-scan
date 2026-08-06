package br.com.bebidasscan.api.avaliacao;

import br.com.bebidasscan.api.avaliacao.dto.AvaliacaoCreateRequest;
import br.com.bebidasscan.api.avaliacao.dto.AvaliacaoResponse;
import br.com.bebidasscan.api.bebida.Bebida;
import br.com.bebidasscan.api.bebida.BebidaRepository;
import br.com.bebidasscan.api.common.ApiException;
import br.com.bebidasscan.api.common.EntityFields;
import br.com.bebidasscan.api.usuario.Usuario;
import java.util.List;
import org.springframework.http.HttpStatus;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

@Service
public class AvaliacaoService {

    private final AvaliacaoRepository avaliacaoRepository;
    private final BebidaRepository bebidaRepository;
    private final AvaliacaoMapper mapper;

    public AvaliacaoService(AvaliacaoRepository avaliacaoRepository, BebidaRepository bebidaRepository, AvaliacaoMapper mapper) {
        this.avaliacaoRepository = avaliacaoRepository;
        this.bebidaRepository = bebidaRepository;
        this.mapper = mapper;
    }

    @Transactional
    public AvaliacaoResponse save(AvaliacaoCreateRequest request, Usuario usuario) {
        Bebida bebida = bebidaRepository.findById(request.idBebida())
                .orElseThrow(() -> new ApiException(HttpStatus.NOT_FOUND, "Bebida nao encontrada"));
        Avaliacao avaliacao = avaliacaoRepository.findByUsuarioOrderByDataAvaliacaoDesc(usuario).stream()
                .filter(item -> bebida.equals(EntityFields.get(item, "bebida", Bebida.class)))
                .findFirst()
                .orElseGet(Avaliacao::new);
        EntityFields.set(avaliacao, "usuario", usuario);
        EntityFields.set(avaliacao, "bebida", bebida);
        EntityFields.set(avaliacao, "nota", request.nota());
        EntityFields.set(avaliacao, "comentario", request.comentario());
        EntityFields.set(avaliacao, "comprariaNovamente", request.comprariaNovamente());
        return mapper.toResponse(avaliacaoRepository.save(avaliacao));
    }

    public List<AvaliacaoResponse> listMine(Usuario usuario) {
        return avaliacaoRepository.findByUsuarioOrderByDataAvaliacaoDesc(usuario).stream()
                .map(mapper::toResponse)
                .toList();
    }
}
