package br.com.bebidasscan.api.privacidade;

import br.com.bebidasscan.api.lgpd.LgpdDocumentService;
import br.com.bebidasscan.api.privacidade.dto.LegalDocumentResponse;
import java.util.Map;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

@RestController
@RequestMapping("/privacidade")
public class PrivacidadeController {

    private final LgpdDocumentService lgpdDocumentService;

    public PrivacidadeController(LgpdDocumentService lgpdDocumentService) {
        this.lgpdDocumentService = lgpdDocumentService;
    }

    @GetMapping("/politica")
    public LegalDocumentResponse politica() {
        return toResponse(lgpdDocumentService.privacyPolicy());
    }

    @GetMapping("/termos")
    public LegalDocumentResponse termos() {
        return toResponse(lgpdDocumentService.termsOfUse());
    }

    private static LegalDocumentResponse toResponse(Map<String, String> document) {
        return new LegalDocumentResponse(document.get("versao"), document.get("texto"));
    }
}
