package br.com.bebidasscan.api.email;

public class EmailNotConfiguredException extends RuntimeException {

    public EmailNotConfiguredException(String message) {
        super(message);
    }
}
