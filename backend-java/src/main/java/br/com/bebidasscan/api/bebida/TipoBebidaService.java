package br.com.bebidasscan.api.bebida;

import java.text.Normalizer;
import org.springframework.stereotype.Service;

@Service
public class TipoBebidaService {

    public String normalize(String value) {
        String text = value == null ? "" : value.trim().toLowerCase();
        return Normalizer.normalize(text, Normalizer.Form.NFD).replaceAll("\\p{M}", "");
    }

    public boolean isCachacaOrAguardente(String value) {
        return normalize(value).matches(".*\\b(cachaca|aguardente)\\b.*");
    }
}
