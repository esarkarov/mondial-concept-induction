import java.io.File;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.util.ArrayList;
import java.util.Collections;
import java.util.List;
import java.util.Set;
import java.util.TreeSet;

import org.coode.owlapi.manchesterowlsyntax.ManchesterOWLSyntaxEditorParser;
import org.dllearner.cli.ExpressionValidation;
import org.dllearner.confparser.ConfParserConfiguration;
import org.dllearner.configuration.spring.DefaultApplicationContextBuilder;
import org.dllearner.core.AbstractClassExpressionLearningProblem;
import org.dllearner.learningproblems.EvaluatedDescriptionPosNeg;
import org.semanticweb.owlapi.apibinding.OWLManager;
import org.semanticweb.owlapi.expression.OWLEntityChecker;
import org.semanticweb.owlapi.expression.ShortFormEntityChecker;
import org.semanticweb.owlapi.model.OWLAnnotationProperty;
import org.semanticweb.owlapi.model.OWLClass;
import org.semanticweb.owlapi.model.OWLClassExpression;
import org.semanticweb.owlapi.model.OWLDataFactory;
import org.semanticweb.owlapi.model.OWLDataProperty;
import org.semanticweb.owlapi.model.OWLDatatype;
import org.semanticweb.owlapi.model.OWLIndividual;
import org.semanticweb.owlapi.model.OWLNamedIndividual;
import org.semanticweb.owlapi.model.OWLObjectProperty;
import org.semanticweb.owlapi.model.OWLOntology;
import org.semanticweb.owlapi.model.OWLOntologyManager;
import org.semanticweb.owlapi.util.BidirectionalShortFormProviderAdapter;
import org.semanticweb.owlapi.util.SimpleShortFormProvider;
import org.springframework.context.ApplicationContext;
import org.springframework.core.io.FileSystemResource;

public class ScoreConcept {

    public static void main(String[] args) throws Exception {
        File conf = new File(args[0]);
        File kb = new File(args[1]);
        List<String[]> items = new ArrayList<>();
        if (args[2].equals("--batch")) {
            for (String line : Files.readAllLines(new File(args[3]).toPath(), StandardCharsets.UTF_8)) {
                if (line.isEmpty()) continue;
                int tab = line.indexOf('\t');
                items.add(new String[] {line.substring(0, tab), line.substring(tab + 1)});
            }
        } else {
            items.add(new String[] {"single", args[2]});
        }

        OWLDataFactory factory = OWLManager.getOWLDataFactory();
        OWLOntologyManager manager = OWLManager.createOWLOntologyManager();
        OWLOntology ontology = manager.loadOntologyFromOntologyDocument(kb);
        BidirectionalShortFormProviderAdapter shortForms = new BidirectionalShortFormProviderAdapter(
                manager, Collections.singleton(ontology), new SimpleShortFormProvider());
        OWLEntityChecker checker = new TopAwareEntityChecker(new ShortFormEntityChecker(shortForms), factory);

        ConfParserConfiguration configuration = new ConfParserConfiguration(new FileSystemResource(conf));
        ApplicationContext context = new DefaultApplicationContextBuilder()
                .buildApplicationContext(configuration, new ArrayList<>());
        ExpressionValidation validation = new ExpressionValidation();
        validation.setContext(context);
        validation.setConfFile(conf);
        validation.setLogLevel("WARN");
        validation.setExpression(factory.getOWLThing());
        validation.init();
        AbstractClassExpressionLearningProblem<?> problem = context.getBean(AbstractClassExpressionLearningProblem.class);

        for (String[] item : items) {
            System.out.println("SCORE_ITEM " + item[0]);
            try {
                ManchesterOWLSyntaxEditorParser parser = new ManchesterOWLSyntaxEditorParser(factory, item[1]);
                parser.setOWLEntityChecker(checker);
                OWLClassExpression expression = parser.parseClassExpression();
                EvaluatedDescriptionPosNeg evaluated = (EvaluatedDescriptionPosNeg) problem.evaluate(expression);
                System.out.println("SCORE_EXPRESSION " + expression);
                System.out.println("SCORE_TP " + names(evaluated.getCoveredPositives()));
                System.out.println("SCORE_FP " + names(evaluated.getCoveredNegatives()));
                System.out.println("SCORE_FN " + names(evaluated.getNotCoveredPositives()));
                System.out.println("SCORE_TN " + names(evaluated.getNotCoveredNegatives()));
            } catch (Exception e) {
                String message = String.valueOf(e.getMessage()).replace('\n', ' ');
                System.out.println("SCORE_ERROR " + e.getClass().getSimpleName() + ": " + message);
            }
            System.out.println("SCORE_END");
        }
    }

    private static class TopAwareEntityChecker implements OWLEntityChecker {
        private final OWLEntityChecker delegate;
        private final OWLDataFactory factory;

        TopAwareEntityChecker(OWLEntityChecker delegate, OWLDataFactory factory) {
            this.delegate = delegate;
            this.factory = factory;
        }

        public OWLClass getOWLClass(String name) {
            if (name.equals("Thing")) return factory.getOWLThing();
            if (name.equals("Nothing")) return factory.getOWLNothing();
            return delegate.getOWLClass(name);
        }

        public OWLObjectProperty getOWLObjectProperty(String name) { return delegate.getOWLObjectProperty(name); }

        public OWLDataProperty getOWLDataProperty(String name) { return delegate.getOWLDataProperty(name); }

        public OWLNamedIndividual getOWLIndividual(String name) { return delegate.getOWLIndividual(name); }

        public OWLDatatype getOWLDatatype(String name) { return delegate.getOWLDatatype(name); }

        public OWLAnnotationProperty getOWLAnnotationProperty(String name) { return delegate.getOWLAnnotationProperty(name); }
    }

    private static String names(Set<OWLIndividual> individuals) {
        TreeSet<String> sorted = new TreeSet<>();
        for (OWLIndividual individual : individuals) {
            sorted.add(individual.asOWLNamedIndividual().getIRI().getFragment());
        }
        return String.join(" ", sorted);
    }
}
