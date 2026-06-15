package com.sde.audit.controller;

import com.sde.audit.dto.ActionRequest;
import com.sde.audit.dto.StatsResponse;
import com.sde.audit.model.Decision;
import com.sde.audit.model.DecisionStatus;
import com.sde.audit.service.DecisionService;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.CrossOrigin;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RequestParam;
import org.springframework.web.bind.annotation.RestController;
import org.springframework.web.server.ResponseStatusException;

import java.util.List;

@RestController
@RequestMapping("/api")
@CrossOrigin(origins = "*")
public class DecisionController {

    private final DecisionService service;

    public DecisionController(DecisionService service) {
        this.service = service;
    }

    /** Ingest a decision from the Python engine. */
    @PostMapping("/decisions")
    @org.springframework.web.bind.annotation.ResponseStatus(HttpStatus.CREATED)
    public Decision create(@RequestBody Decision decision) {
        return service.record(decision);
    }

    /** List decisions, newest first. Optional ?status=PENDING|APPROVED|OVERRIDDEN|ESCALATED */
    @GetMapping("/decisions")
    public List<Decision> list(@RequestParam(required = false) DecisionStatus status) {
        return service.list(status);
    }

    @GetMapping("/decisions/{id}")
    public Decision get(@PathVariable Long id) {
        return service.get(id)
                .orElseThrow(() -> new ResponseStatusException(HttpStatus.NOT_FOUND, "decision not found"));
    }

    /** Record an agent action (APPROVE / OVERRIDE / ESCALATE). */
    @PostMapping("/decisions/{id}/action")
    public Decision action(@PathVariable Long id, @RequestBody ActionRequest request) {
        try {
            return service.applyAction(id, request)
                    .orElseThrow(() -> new ResponseStatusException(HttpStatus.NOT_FOUND, "decision not found"));
        } catch (IllegalArgumentException e) {
            throw new ResponseStatusException(HttpStatus.BAD_REQUEST, e.getMessage());
        }
    }

    /** Dashboard summary + feedback-loop view. */
    @GetMapping("/stats")
    public StatsResponse stats() {
        return service.stats();
    }

    @GetMapping("/health")
    public ResponseEntity<String> health() {
        return ResponseEntity.ok("ok");
    }
}
