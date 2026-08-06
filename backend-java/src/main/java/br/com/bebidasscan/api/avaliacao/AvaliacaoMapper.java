package br.com.bebidasscan.api.avaliacao;

import br.com.bebidasscan.api.avaliacao.dto.AvaliacaoResponse;
import br.com.bebidasscan.api.bebida.Bebida;
import br.com.bebidasscan.api.common.EntityFields;
import java.time.LocalDateTime;
import org.springframework.stereotype.Component;

@Component
public class AvaliacaoMapper {

    public AvaliacaoResponse toResponse(Avaliacao avaliacao) {
        Bebida bebida = EntityFields.get(avaliacao, "bebida", Bebida.class);
        return new AvaliacaoResponse(
                EntityFields.get(avaliacao, "idAvaliacao", Integer.class),
                bebida == null ? null : bebida.getIdBebida(),
                EntityFields.get(avaliacao, "nota", Integer.class),
                EntityFields.get(avaliacao, "comentario", String.class),
                EntityFields.get(avaliacao, "comprariaNovamente", Boolean.class),
                EntityFields.get(avaliacao, "dataAvaliacao", LocalDateTime.class)
        );
    }
}
