package br.com.bebidasscan.api.bebida;

import br.com.bebidasscan.api.bebida.dto.BebidaResponse;
import br.com.bebidasscan.api.bebida.dto.CachacaResponse;
import br.com.bebidasscan.api.common.EntityFields;
import br.com.bebidasscan.api.usuario.Usuario;
import java.math.BigDecimal;
import org.springframework.stereotype.Component;

@Component
public class BebidaMapper {

    public BebidaResponse toResponse(Bebida bebida) {
        Cachaca cachaca = EntityFields.get(bebida, "cachaca", Cachaca.class);
        Usuario criadoPor = EntityFields.get(bebida, "criadoPor", Usuario.class);
        return new BebidaResponse(
                bebida.getIdBebida(),
                bebida.getNome(),
                EntityFields.get(bebida, "marca", String.class),
                EntityFields.get(bebida, "tipo", String.class),
                bebida.getCodigoBarras(),
                EntityFields.get(bebida, "teorAlcoolico", BigDecimal.class),
                EntityFields.get(bebida, "ingredientes", String.class),
                EntityFields.get(bebida, "imagemUrl", String.class),
                EntityFields.get(bebida, "nutriScore", String.class),
                EntityFields.get(bebida, "novaGrupo", Integer.class),
                EntityFields.get(bebida, "ecoScore", String.class),
                EntityFields.get(bebida, "alergenos", String.class),
                EntityFields.get(bebida, "categorias", String.class),
                EntityFields.get(bebida, "quantidade", String.class),
                EntityFields.get(bebida, "embalagem", String.class),
                EntityFields.get(bebida, "paises", String.class),
                cachaca == null ? null : toResponse(cachaca),
                EntityFields.get(bebida, "origemDados", String.class),
                criadoPor == null ? null : criadoPor.getIdUsuario()
        );
    }

    public CachacaResponse toResponse(Cachaca cachaca) {
        Bebida bebida = EntityFields.get(cachaca, "bebida", Bebida.class);
        return new CachacaResponse(
                EntityFields.get(cachaca, "idCachaca", Integer.class),
                bebida == null ? null : bebida.getIdBebida(),
                EntityFields.get(cachaca, "volumeMl", Integer.class),
                EntityFields.get(cachaca, "classificacao", String.class),
                EntityFields.get(cachaca, "madeira", String.class),
                EntityFields.get(cachaca, "tempoEnvelhecimentoMeses", Integer.class),
                EntityFields.get(cachaca, "cidadeOrigem", String.class),
                EntityFields.get(cachaca, "estadoOrigem", String.class),
                EntityFields.get(cachaca, "regiaoOrigem", String.class),
                EntityFields.get(cachaca, "alambique", String.class),
                EntityFields.get(cachaca, "produtor", String.class),
                EntityFields.get(cachaca, "lote", String.class)
        );
    }
}
