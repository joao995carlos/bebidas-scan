package br.com.bebidasscan.api.lgpd;

import br.com.bebidasscan.api.common.EntityFields;
import br.com.bebidasscan.api.perfil.dto.LgpdStatusResponse;
import br.com.bebidasscan.api.usuario.Usuario;
import java.time.LocalDate;
import java.time.LocalDateTime;
import java.time.Period;
import java.time.ZoneOffset;
import org.springframework.stereotype.Service;

@Service
public class LgpdService {

    public boolean isAdult(LocalDate birthDate) {
        return birthDate != null && Period.between(birthDate, LocalDate.now()).getYears() >= 18;
    }

    public boolean isPending(Usuario usuario) {
        return EntityFields.get(usuario, "dataNascimento", LocalDate.class) == null
                || !Boolean.TRUE.equals(EntityFields.get(usuario, "confirmouMaioridade", Boolean.class))
                || !LgpdDocumentService.DOCUMENT_VERSION.equals(EntityFields.get(usuario, "privacidadeVersaoAceita", String.class))
                || !LgpdDocumentService.DOCUMENT_VERSION.equals(EntityFields.get(usuario, "termosVersaoAceita", String.class))
                || EntityFields.get(usuario, "lgpdAceiteEm", LocalDateTime.class) == null;
    }

    public void applyAcceptance(Usuario usuario, LocalDate birthDate, boolean marketingConsent) {
        EntityFields.set(usuario, "dataNascimento", birthDate);
        EntityFields.set(usuario, "confirmouMaioridade", isAdult(birthDate));
        EntityFields.set(usuario, "privacidadeVersaoAceita", LgpdDocumentService.DOCUMENT_VERSION);
        EntityFields.set(usuario, "termosVersaoAceita", LgpdDocumentService.DOCUMENT_VERSION);
        EntityFields.set(usuario, "lgpdAceiteEm", LocalDateTime.now(ZoneOffset.UTC));
        EntityFields.set(usuario, "marketingConsentimento", marketingConsent);
        EntityFields.set(usuario, "marketingConsentimentoEm", marketingConsent ? LocalDateTime.now(ZoneOffset.UTC) : null);
    }

    public LgpdStatusResponse status(Usuario usuario) {
        return new LgpdStatusResponse(
                isPending(usuario),
                LgpdDocumentService.DOCUMENT_VERSION,
                EntityFields.get(usuario, "privacidadeVersaoAceita", String.class),
                EntityFields.get(usuario, "termosVersaoAceita", String.class),
                EntityFields.get(usuario, "lgpdAceiteEm", LocalDateTime.class)
        );
    }
}
