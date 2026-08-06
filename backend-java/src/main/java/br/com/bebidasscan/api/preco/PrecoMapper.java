package br.com.bebidasscan.api.preco;

import br.com.bebidasscan.api.bebida.Bebida;
import br.com.bebidasscan.api.common.EntityFields;
import br.com.bebidasscan.api.preco.dto.PrecoResponse;
import java.math.BigDecimal;
import java.time.LocalDateTime;
import org.springframework.stereotype.Component;

@Component
public class PrecoMapper {

    public PrecoResponse toResponse(Preco preco) {
        Bebida bebida = EntityFields.get(preco, "bebida", Bebida.class);
        return new PrecoResponse(
                EntityFields.get(preco, "idPreco", Integer.class),
                bebida == null ? null : bebida.getIdBebida(),
                EntityFields.get(preco, "mercado", String.class),
                EntityFields.get(preco, "cidade", String.class),
                EntityFields.get(preco, "estado", String.class),
                EntityFields.get(preco, "valor", BigDecimal.class),
                EntityFields.get(preco, "dataRegistro", LocalDateTime.class)
        );
    }
}
